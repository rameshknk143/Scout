import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from registry.observation_store import ObservationStore, snapshot_records, deliver
from registry.source_adapters import sales_traffic_report, derive, estimate, INDIA_MARKETPLACE_ID

ASIN='B012345678'
ROW={'asin':ASIN,'title':'Laptop','category':'Electronics','subcategory':'Computers & Accessories',
     'product_type':'laptop','price':1000,'rating':4.2,'review_count':7,'rank':2,
     'collected_at':'2026-10-06T20:00:00Z','source':'collector','list_type':'bestsellers'}

class FieldStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'fields.sqlite';self.store=ObservationStore(self.path)

    def test_durable_replay_preserves_distinct_capture_times(self):
        first=self.store.enqueue([ROW]);self.assertGreater(first,0)
        self.assertEqual(self.store.enqueue([ROW]),0)
        again=ObservationStore(self.path)
        self.assertEqual(again.status()['pending_delivery'],first)
        later={**ROW,'collected_at':'2026-10-06T21:00:00Z','price':900}
        self.assertEqual(again.enqueue([later]),first)
        prices=[r for r in again.pending() if r['field_key']=='price']
        self.assertEqual([r['normalized_value'] for r in prices],[1000,900])

    def test_list_rank_never_becomes_bsr(self):
        records=snapshot_records(ROW)
        self.assertNotIn('bsr',[r['field_key'] for r in records])
        self.assertTrue(all(r['context']['list_rank']==2 for r in records))

    def test_title_inference_is_not_published_brand_or_classification(self):
        records=snapshot_records({**ROW,'brand':'Example'})
        statuses={r['field_key']:r['status'] for r in records}
        self.assertEqual(statuses['brand'],'INFERRED')
        self.assertEqual(statuses['product_type'],'INFERRED')
        self.assertEqual(statuses['price'],'COLLECTED')

    def test_naive_timestamp_and_bad_asin_rejected(self):
        for row in [{**ROW,'collected_at':'2026-10-06T20:00:00'},{**ROW,'asin':'bad'}]:
            with self.assertRaises(ValueError):self.store.enqueue([row])
        self.assertEqual(self.store.status()['total_observations'],0)

    def test_unknown_labels_and_incompatible_fields_are_retained(self):
        row={**ROW,'attribute_observations':{'observations':[{'field_key':'garment_size','raw_value':'XL','status':'COLLECTED','normalized_value':'XL'}],
            'unmapped':[{'label':'New attribute','raw_value':'original'}]}}
        self.store.enqueue([row]);records=self.store.pending()
        size=next(r for r in records if r['field_key']=='garment_size')
        self.assertEqual(size['status'],'NOT_APPLICABLE')
        self.assertIsNone(size['normalized_value'])
        self.assertTrue(any(r['field_key']=='unreviewed:New attribute' for r in records))

    def test_private_metric_cannot_be_spoofed_as_public_collected(self):
        row={**ROW,'attribute_observations':{'observations':[{'field_key':'unit_session_percentage','raw_value':50,'normalized_value':50,'status':'COLLECTED'}]}}
        self.store.enqueue([row]);record=next(r for r in self.store.pending() if r['field_key']=='unit_session_percentage')
        self.assertEqual(record['status'],'WRONG_COLLECTION_SOURCE');self.assertIsNone(record['normalized_value'])

    def test_missing_migration_keeps_pending_data(self):
        self.store.enqueue([ROW]);cursor=MagicMock();cursor.fetchone.return_value=(None,)
        self.assertEqual(deliver(cursor,self.store.pending()),[])
        self.assertGreater(self.store.status()['pending_delivery'],0)

    def test_acknowledgement_is_specific_and_preserves_local_history(self):
        self.store.enqueue([ROW]);pending=self.store.pending();count=len(pending)
        self.store.acknowledge([pending[0]['observation_id']])
        self.assertEqual(self.store.status(),{'total_observations':count,'pending_delivery':count-1,'path':str(self.path)})

    def test_tampered_normalized_spec_is_recomputed_from_raw(self):
        row={**ROW,'attribute_observations':{'observations':[{'field_key':'ram','raw_value':'8 GB','normalized_value':999,'status':'COLLECTED'}]}}
        self.store.enqueue([row]);record=next(r for r in self.store.pending() if r['field_key']=='ram')
        self.assertEqual(record['normalized_value'],8_000_000_000)

    def test_report_owner_marketplace_and_child_identity_required(self):
        report={'reportSpecification':{'reportType':'GET_SALES_AND_TRAFFIC_REPORT','marketplaceIds':[INDIA_MARKETPLACE_ID],
                    'reportOptions':{'asinGranularity':'CHILD'},'dataStartTime':'2026-09-01T00:00:00Z','dataEndTime':'2026-09-30T23:59:59Z'},
                 'salesAndTrafficByAsin':[{'childAsin':ASIN,'trafficByAsin':{'unitSessionPercentage':125,'buyBoxPercentage':90}}]}
        args={'seller_id':'owned-test-seller','report_id':'test-report','authorized_asins':[ASIN]}
        records=sales_traffic_report(report,**args)
        self.assertEqual(records[0]['normalized_value'],125)
        self.assertEqual(records[0]['source'],'authorized_seller_report')
        self.store.enqueue_records(records);self.assertEqual(self.store.status()['pending_delivery'],2)
        with self.assertRaises(ValueError):sales_traffic_report(report,**{**args,'authorized_asins':[]})
        report['reportSpecification']['reportOptions']['asinGranularity']='PARENT'
        with self.assertRaises(ValueError):sales_traffic_report(report,**args)

    def test_derived_and_estimated_values_have_explicit_provenance(self):
        self.assertEqual(derive({'price':50,'list_price':100})['discount_percentage']['value'],50)
        self.assertEqual(derive({'price':50}),{})
        self.assertNotIn('estimated_monthly_units',derive({'bsr':1}))
        with self.assertRaises(ValueError):estimate(50,model_id='',model_version='',confidence=.8,period_start='x',period_end='y',input_ids=[])
        value=estimate(50,model_id='model',model_version='1',confidence=.8,period_start='2026-09-01',period_end='2026-09-30',input_ids=['observation'])
        self.assertEqual(value['status'],'ESTIMATED')

if __name__=='__main__':unittest.main()
