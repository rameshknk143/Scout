"""Versioned category -> product type -> extraction plan and reverse lookup.

Schemas describe requirements, not extractor implementation or guaranteed availability.
Unknown conditions remain PENDING_CONTEXT; protected/private routes never become public jobs.
"""
import argparse
import copy
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name('amazon_schema.json')
PROFILE_CATEGORIES = {
 'computer':['Electronics'], 'mobile_computer':['Electronics'], 'audio':['Electronics','Musical Instruments'],
 'television':['Electronics'], 'camera':['Electronics'], 'lens':['Electronics'],
 'computer_component':['Electronics'], 'storage':['Electronics'], 'charger':['Electronics','Automotive'],
 'cable':['Electronics','Automotive','Musical Instruments'], 'phone_case':['Electronics'],
 'clothing':['Apparel','Baby','Sports','Boost'], 'footwear':['Shoes','Sports','Baby'],
 'watch':['Watches'], 'smart_watch':['Watches','Electronics','Sports'], 'jewelry':['Jewelry'],
 'bag':['Luggage','Sports','Apparel','Office'], 'food':['Grocery','Pet Supplies','Baby','Boost'],
 'supplement':['Hpc','Grocery','Sports'], 'medicine':['Hpc'], 'beauty':['Beauty','Hpc','Baby'],
 'paint_chemical':['Home Improvement','Industrial','Garden','Hpc','Automotive'],
 'furniture':['Kitchen','Garden','Office','Baby'], 'textile':['Kitchen','Baby','Sports'],
 'cookware':['Kitchen'], 'appliance':['Kitchen','Hpc','Beauty'], 'light':['Kitchen','Home Improvement','Automotive'],
 'sport_equipment':['Sports'], 'toy':['Toys','Baby','Boost'], 'baby_gear':['Baby'], 'feeding':['Baby','Kitchen'],
 'pet_accessory':['Pet Supplies'], 'automotive_part':['Automotive'], 'tool':['Industrial','Home Improvement','Garden'],
 'garden':['Garden'], 'book':['Books'], 'digital_book':['Books'], 'physical_media':['Dvd','Music','Videogames'],
 'digital_media':['Software','Mobile Apps','Music','Dvd','Videogames'], 'gift_card':['Gift Cards'],
 'musical_instrument':['Musical Instruments'], 'stationery':['Office'],
}
PROFILE_ALIASES = {'wireless earbuds':'wireless_earbuds','over ear':'over_ear','t-shirt':'tshirt',
                   't shirt':'tshirt','smartwatch':'smart_watch','phone case':'phone_case',
                   'power bank':'power_bank','e-book':'ebook','earphones':'wired_headphones'}
for _profile in ('computer','mobile_computer','audio','computer_component','storage','charger','cable'):
    PROFILE_CATEGORIES[_profile].append('Computers & Accessories')
PROFILE_CATEGORIES['digital_book'].append('Kindle Store')
for _profile in ('computer','mobile_computer','audio','television','camera','lens','computer_component','storage','charger','cable','smart_watch','watch','appliance','tool','musical_instrument'):
    PROFILE_CATEGORIES[_profile].append('Amazon Renewed')
SPEC_ALIASES = {'ram size':'ram','installed ram memory size':'ram','ram memory installed size':'ram',
 'brand name':'brand','box contents':'included_components','impedance unit of measure':'impedance',
 'memory storage capacity':'storage','hard drive size':'storage','digital storage capacity':'storage',
 'cpu model':'processor','processor type':'processor','screen size':'screen_size','display size':'screen_size',
 'item weight':'weight','material type':'material','material composition':'fabric_composition',
 'fabric type':'fabric_composition','shoe width':'fit_type','ingredients':'ingredients_components',
 'included components':'included_components','item model number':'model_number',
 'manufacturer':'manufacturer','country of origin':'country_of_origin','warranty description':'warranty',
 'connector type':'connector_type','hardware interface':'storage_interface','battery capacity':'battery_capacity'}

def token(value):
    return re.sub(r'\s+', ' ', str(value or '').strip().lower())

class AmazonSchema:
    def __init__(self, path=SCHEMA_PATH):
        self.data=json.loads(Path(path).read_text(encoding='utf-8'))
        self.fields={**self.data['fields'], **self.data['extensions']}
        self.tops={token(n['top']):n['top'] for n in self.data['taxonomy']}
        self.tops.update({token(n['label']):n['label'] for n in self.data.get('top_routes',[])})
        self.by_path={token(n['label']):n for n in self.data['taxonomy']}
        self.by_node={}
        for n in self.data['taxonomy']:
            self.by_node.setdefault(str(n['node']),[]).append(n)
            for legacy in n.get('legacy_nodes',[]):
                self.by_node.setdefault(str(legacy),[]).append({**n,'legacy_match':True})
        self.validate()

    def validate(self):
        points=self.data['source_points']
        if [p['source_id'] for p in points] != list(range(1,296)):
            raise ValueError('Master source IDs are incomplete or duplicated')
        for p in points:
            if p['field_key'] not in self.fields or p['source_id'] not in self.fields[p['field_key']]['source_ids']:
                raise ValueError('Broken source-to-canonical relationship')
        for key,f in self.fields.items():
            if f['key']!=key or any(dep not in self.fields for dep in f['dependencies']):
                raise ValueError('Invalid key or dependency: '+key)
        if set(PROFILE_CATEGORIES)!=set(self.data['profiles']):
            raise ValueError('Profile category constraints out of sync')
        if any(p.get('categories')!=PROFILE_CATEGORIES[k] for k,p in self.data['profiles'].items()):
            raise ValueError('Rebuild schema after profile category changes')

    def resolve_category(self, category, subcategory=None, node=None):
        raw=str(category or '').strip()
        parts=[x.strip() for x in raw.split('>')]
        top=self.tops.get(token(parts[0])) or self.data['category_aliases'].get(token(parts[0]))
        leaf=subcategory or (parts[1] if len(parts)>1 else None)
        if node is not None:
            candidates=self.by_node.get(str(node),[])
            candidates=[n for n in candidates if not top or n['top']==top]
            if len(candidates)==1:
                n=candidates[0]
                return {'top':n['top'],'leaf':n['leaf'],'node':n['node'],'path':n['label'],
                        'status':'LEGACY_NODE_REDIRECT' if n.get('legacy_match') else 'SNAPSHOT_MATCH'}
            return {'top':top,'leaf':leaf,'node':str(node),'path':raw,'status':'UNKNOWN_OR_AMBIGUOUS_NODE'}
        n=self.by_path.get(token(f'{top} > {leaf}')) if top and leaf else None
        status='SNAPSHOT_MATCH' if n and len(parts)<=2 else 'TOP_ONLY' if top and not leaf else 'UNKNOWN_PATH'
        return {'top':top,'leaf':leaf,'node':n['node'] if n and status=='SNAPSHOT_MATCH' else None,
                'path':n['label'] if n and status=='SNAPSHOT_MATCH' else raw,'status':status}

    def plan(self, category, subcategory=None, product_type=None, *, node=None,
             product_form=None, has_variants=None, fulfillment=None,
             has_subscription=None, enabled_sources=('product_page','technical_specs'),
             verified_fee_policy=False, tier_limit=3):
        ctx=self.resolve_category(category,subcategory,node)
        if not subcategory and token(category)=='computers & accessories' and not self.data.get('top_routes'):
            ctx=self.resolve_category('Electronics','Computers & Accessories',node)
        pt=PROFILE_ALIASES.get(token(product_type),token(product_type).replace(' ','_'))
        candidates=[k for k,p in self.data['profiles'].items() if ctx['top'] in p['categories']
                    and (ctx['leaf'] is None or ctx['top'] not in p.get('subcategory_constraints',{})
                         or ctx['leaf'] in p['subcategory_constraints'][ctx['top']])]
        profiles=[k for k in candidates if pt in self.data['profiles'][k]['product_types']]
        traits={t for p in profiles for t in self.data['profiles'][p]['traits']}
        traits.update(t for p in profiles for t in self.data['profiles'][p].get('product_traits',{}).get(pt,[]))
        if product_form not in {None,'physical','digital'}:
            raise ValueError('product_form must be physical or digital')
        if product_form and profiles and ('physical' if product_form=='digital' else 'digital') in traits:
            raise ValueError('Product form conflicts with product-type profile')
        if product_form:
            traits.discard('physical' if product_form=='digital' else 'digital');traits.add(product_form)
        # Only intrinsically physical categories default to physical. Mixed digital/media categories need context.
        physical_tops={'Electronics','Apparel','Automotive','Baby','Beauty','Garden','Grocery','Home Improvement','Hpc','Industrial','Jewelry','Kitchen','Luggage','Musical Instruments','Office','Pet Supplies','Shoes','Sports','Toys','Watches'}
        if not ({'physical','digital'} & traits) and ctx['top'] in physical_tops:
            traits.add('physical')
        if ctx['top']=='Mobile Apps':traits.add('digital')
        # These traits are unambiguous at a whole-category level.
        if ctx['top']=='Grocery':traits.update({'ingredients','consumable'})
        if ctx['top'] in {'Apparel','Shoes','Jewelry'}:traits.update({'fit','wearable','care'})
        supported=set(enabled_sources); result={}
        for key,f in self.fields.items():
            if f['tier']>tier_limit:continue
            app=f.get('applicability',{})
            c=app.get('condition','any')
            state='APPLICABLE'; reason='Shared commercial/product field across categories.'
            if 'profiles' in f:
                if set(profiles)&set(f['profiles']):reason='Exact product-type profile: '+', '.join(profiles)
                elif profiles: state='NOT_APPLICABLE';reason='Specification belongs to another product-type profile.'
                else: state='PENDING_CONTEXT';reason='Product type must be identified before assigning this specification.'
            elif c=='physical':
                if 'digital' in traits:state='NOT_APPLICABLE';reason='Digital delivery has no physical dimensions, packaging or inventory.'
                elif 'physical' not in traits:state='PENDING_CONTEXT';reason='Physical/digital product form needed.'
                else:reason='Physical product/fulfillment field.'
            elif c=='variant_family':
                if has_variants is False:state='NOT_APPLICABLE';reason='Confirmed product has no variant family.'
                elif has_variants is None:state='PENDING_CONTEXT';reason='Published variant family must be confirmed.'
                else:reason='Confirmed variant family; preserve child ASIN and variation theme.'
            elif c=='subscription_offer':
                if has_subscription is False:state='NOT_APPLICABLE';reason='No Subscribe & Save offer.'
                elif has_subscription is None:state='PENDING_CONTEXT';reason='Subscription offer must be confirmed.'
            elif c!='any':
                if c in traits:reason='Relevant product trait: '+c
                elif profiles or 'digital' in traits:state='NOT_APPLICABLE';reason='Product profile lacks trait: '+c
                else:state='PENDING_CONTEXT';reason='Need product profile/trait: '+c
            if state=='APPLICABLE' and app.get('requires_fba'):
                if fulfillment is None:state='PENDING_CONTEXT';reason='FBA fulfillment must be confirmed.'
                elif token(fulfillment)!='fba':state='NOT_APPLICABLE';reason='FBA-only metric/fee on a non-FBA offer.'
            if state=='APPLICABLE' and f.get('requires_trait') and f['requires_trait'] not in traits:
                state='PENDING_CONTEXT';reason='Confirm product trait before collecting: '+f['requires_trait']
            if state=='APPLICABLE' and app.get('requires_verified_marketplace_policy') and not verified_fee_policy:
                state='PENDING_POLICY';reason='Verify effective India fee policy before using this fee.'
            source=f['source']
            initial='NOT_APPLICABLE' if state=='NOT_APPLICABLE' else 'PENDING_CONTEXT' if state=='PENDING_CONTEXT' else 'PENDING_POLICY' if state=='PENDING_POLICY' else (
                'NOT_PUBLICLY_AVAILABLE' if source=='unavailable' else 'MISSING' if source in supported
                else 'REQUIRES_SELLER_ACCOUNT' if source=='seller_report' else 'REQUIRES_INPUTS' if source in {'derived','history','estimate'} else 'REQUIRES_EXTERNAL_SOURCE')
            result[key]={**copy.deepcopy(f),'applicability_status':state,'reason':reason,'initial_status':initial,
                         'collect_now':state=='APPLICABLE' and source in supported and source!='unavailable'}
        return {'schema_version':self.data['schema_version'],'marketplace':self.data['marketplace'],
          'category':ctx,'product_type':pt or None,'profiles':profiles,'candidate_profiles':candidates,'traits':sorted(traits),
          'warnings':(['Product type is unknown or incompatible with category; specialized fields await review.'] if not profiles else [])+
                     (['Category path is not a verified snapshot path.'] if ctx['status'] not in {'SNAPSHOT_MATCH','TOP_ONLY'} else []),
          'fields':result}

    def categories_for_field(self, key, include_conditional=True):
        if key not in self.fields:raise KeyError(key)
        rows=[]
        for n in self.data['taxonomy']:
            plan=self.plan(n['top'],n['leaf']); f=plan['fields'][key]
            if f['applicability_status']=='NOT_APPLICABLE':continue
            if not include_conditional and f['applicability_status']!='APPLICABLE':continue
            profile_matches=[p for p in self.fields[key].get('profiles',[]) if p in plan['candidate_profiles']]
            if self.fields[key].get('profiles') and not profile_matches:continue
            rows.append({'path':n['label'],'node':n['node'],'status':f['applicability_status'],
                         'product_profiles':profile_matches,'condition':self.fields[key].get('applicability',{})})
        # A valid top-level profile may have no matching leaf in the incomplete
        # snapshot (e.g. camera lenses). Keep that relationship visible without
        # inventing a leaf/node or assigning it to unrelated subcategories.
        if include_conditional:
            covered={p for row in rows for p in row['product_profiles']}
            for profile in self.fields[key].get('profiles',[]):
                if profile in covered:continue
                for top in self.data['profiles'][profile]['categories']:
                    rows.append({'path':top,'node':None,'status':'PENDING_TAXONOMY',
                                 'product_profiles':[profile],'condition':{},
                                 'reason':'Product profile is relevant; snapshot has no approved matching leaf.'})
        return rows

    def audit(self):
        counts={}
        for f in self.fields.values():
            counts[f['source']]=counts.get(f['source'],0)+1
        return {**self.data['source_audit'],'top_categories':len(self.tops),'saved_subcategory_paths':len(self.data['taxonomy']),
          'product_profiles':len(self.data['profiles']), 'supported_product_type_labels':len({t for p in self.data['profiles'].values() for t in p['product_types']}),
          'classification_counts':{c:sum(f['classification']==c for f in self.fields.values()) for c in ['universal','conditional','product_type_specific']},
          'source_counts':counts,'duplicate_source_aliases':{k:f['source_ids'] for k,f in self.data['fields'].items() if len(f['source_ids'])>1},
          'unmapped_defined_source_points':0,'production_ready':False}

    def extract_specifications(self, pairs, *, category, product_type=None,
                               source_url, context=None):
        """Apply the schema to published label/value pairs; quarantine unknown labels.

        No keyword/title guesses, silent overwrites, incompatible-profile values or
        default numeric units. Raw unknown specifications remain available for review.
        """
        plan=self.plan(category, product_type=product_type, **(context or {}))
        aliases={token(f['label']):k for k,f in self.fields.items()}
        aliases.update({token(k.replace('_',' ')):k for k in self.fields})
        aliases.update(SPEC_ALIASES)
        observations=[];unmapped=[]
        for label, raw in pairs:
            key=aliases.get(token(label))
            if not key:
                unmapped.append({'label':label,'raw_value':raw,'status':'UNREVIEWED_ATTRIBUTE'});continue
            f=plan['fields'][key]
            if f['source'] not in {'product_page','technical_specs'}:
                unmapped.append({'label':label,'raw_value':raw,'status':'WRONG_COLLECTION_SOURCE','field_key':key});continue
            record=self.observation(key,raw,category=category,product_type=product_type,
                                    source_url=source_url,context=context)
            record['raw_label']=label;observations.append(record)
        return {'schema_version':plan['schema_version'],'category':plan['category'],
                'profiles':plan['profiles'],'observations':observations,'unmapped':unmapped,
                'warnings':plan['warnings']}

    def observation(self, key, raw, *, source_url, category, product_type=None,
                    context=None, observed_at=None, unit=None):
        """Validate a typed value without losing the original; no fabricated fallback."""
        plan=self.plan(category,product_type=product_type,**(context or {}))
        f=plan['fields'][key]
        out={'schema_version':self.data['schema_version'],'field_key':key,'raw_value':raw,
          'source_unit':unit,
          'normalized_value':None,'unit':unit or f['unit'],'scope':f['scope'], 'source_url':source_url,
          'observed_at':observed_at or datetime.now(timezone.utc).isoformat(),'status':f['initial_status']}
        if f['applicability_status']!='APPLICABLE':return out
        if raw is None:out['status']='MISSING';return out
        try:
            value=self.normalize(f,raw,unit)
            out['normalized_value']=value
            out['unit']=f['unit'] or unit
            # This API accepts observed public values only; calculation/report adapters must provide their provenance separately.
            if f['source'] not in {'product_page','technical_specs'}:
                raise ValueError('Use the source-specific adapter with report/model/input provenance')
            out['status']='COLLECTED'
        except (ValueError,TypeError,ArithmeticError) as exc:
            out['normalized_value']=None;out['status']='FAILED';out['error']=str(exc)
        return out

    @staticmethod
    def normalize(f, raw, unit=None):
        dtype=f['value_type'];target=f.get('unit')
        if dtype=='boolean':
            if type(raw) is not bool:raise ValueError('Boolean requires an explicit true/false value')
            return raw
        if dtype in {'number','integer'}:
            if isinstance(raw,bool):raise ValueError('Boolean is not a numeric observation')
            text=str(raw).strip()
            match=re.fullmatch(r'([+-]?\d+(?:\.\d+)?)\s*([A-Za-z]+)?',text)
            if not match:raise ValueError('Ambiguous or invalid numeric value; parse currency/ranges in source adapter')
            value=Decimal(match[1]); given=unit or match[2]
            unit_aliases={'grams':'g','gram':'g','kilograms':'kg','kilogram':'kg','centimeters':'cm','centimetres':'cm',
                          'millimeters':'mm','millimetres':'mm','inches':'inch','ohms':'ohm','watts':'w','volts':'v'}
            if given:given=unit_aliases.get(token(given),given)
            if unit and match[2] and token(unit)!=token(match[2]):raise ValueError('Conflicting supplied and raw units')
            conversions={'cm':{'mm':Decimal('.1'),'cm':Decimal(1),'m':Decimal(100),'inch':Decimal('2.54'),'in':Decimal('2.54')},
              'g':{'g':Decimal(1),'kg':Decimal(1000)}, 'kg':{'g':Decimal('.001'),'kg':Decimal(1)},
              'bytes':{'bytes':Decimal(1),'kb':Decimal(1000),'mb':Decimal(10**6),'gb':Decimal(10**9),'tb':Decimal(10**12),'kib':Decimal(1024),'mib':Decimal(1024**2),'gib':Decimal(1024**3),'tib':Decimal(1024**4)}}
            if target=='context_required':raise ValueError('Capacity needs a semantic unit: litres, storage, seats, etc.')
            if target in conversions:
                if not given or token(given) not in conversions[target]:raise ValueError('Explicit compatible measurement unit required')
                value*=conversions[target][token(given)]
            elif given and target and token(given)!=token(target):raise ValueError('Unit conversion is not defined')
            if not value.is_finite() or (value<0 and not f.get('negative_allowed')):raise ValueError('Non-finite or invalid negative value')
            if f.get('bounded_percentage') and value>100:raise ValueError('Percentage outside 0..100')
            if f['key'] in {'rating','review_rating'} and value>5:raise ValueError('Rating outside 0..5')
            if dtype=='integer':
                if value!=value.to_integral_value():raise ValueError('Integer required')
                return int(value)
            return float(value)
        if dtype=='array':
            if isinstance(raw,str) and f['key'] in {'included_components','ingredients_components','material','compatible_models'}:
                if not raw.strip():raise ValueError('Empty published specification')
                return [raw.strip()]
            if not isinstance(raw,list):raise ValueError('Array required')
            return copy.deepcopy(raw)
        if dtype=='object':
            if not isinstance(raw,dict):raise ValueError('Object required')
            return copy.deepcopy(raw)
        if dtype=='date':
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(raw)):raise ValueError('ISO date required')
            datetime.strptime(raw,'%Y-%m-%d');return raw
        if dtype=='url' and not re.match(r'^https?://[^\s/]+(?:/[^\s]*)?$',str(raw)):
            raise ValueError('HTTP(S) URL required')
        if not isinstance(raw,str):raise ValueError('String required')
        if f['key'] in {'asin','parent_asin'} and not re.fullmatch(r'[A-Z0-9]{10}',raw.strip()):
            raise ValueError('Ten-character ASIN required')
        return raw.strip()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--audit',action='store_true')
    parser.add_argument('--category');parser.add_argument('--subcategory');parser.add_argument('--product-type')
    parser.add_argument('--field');args=parser.parse_args();schema=AmazonSchema()
    result=schema.audit() if args.audit else schema.categories_for_field(args.field) if args.field else schema.plan(args.category,args.subcategory,args.product_type)
    print(json.dumps(result,indent=2,ensure_ascii=True))
