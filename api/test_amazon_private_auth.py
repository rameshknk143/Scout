import os
import unittest
from unittest.mock import Mock, patch
from amazon_private_auth import restore_token, AuthorizationFailure


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.db.get_seller_credentials.return_value = [{'selling_partner_id':'seller', 'marketplace_id':'A21TJRUUN4KGV'}]
        self.session = Mock()
        self.session.post.return_value.status_code = 200
        self.session.post.return_value.json.return_value = {'access_token':'private-access'}
        self.session.get.return_value.status_code = 200
        self.session.get.return_value.json.return_value = {'items':[{'asin':'B012345678'}]}
        self.env = patch.dict(os.environ, {'LWA_CLIENT_ID':'client','LWA_CLIENT_SECRET':'secret'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_success_validates_before_encrypted_storage(self):
        self.assertTrue(restore_token('Atzr|example', 1, self.db, self.session)['catalog_access'])
        self.db.save_seller_credentials.assert_called_once_with('seller','Atzr|example',1,'A21TJRUUN4KGV')
        self.assertEqual(self.session.get.call_args.kwargs['timeout'], (10,40))

    def test_denial_retains_existing_secret(self):
        for stage in ('post','get'):
            with self.subTest(stage=stage):
                self.session.post.return_value.status_code = 200
                self.session.get.return_value.status_code = 200
                getattr(self.session, stage).return_value.status_code = 403
                with self.assertRaises(AuthorizationFailure) as error:
                    restore_token('Atzr|example', 1, self.db, self.session)
                self.assertNotIn('Atzr|example', str(error.exception))
                self.db.save_seller_credentials.assert_not_called()

    def test_wrong_account_count_fails_closed(self):
        self.db.get_seller_credentials.return_value = []
        with self.assertRaises(AuthorizationFailure):
            restore_token('Atzr|example',1,self.db,self.session)
        self.session.post.assert_not_called()

    def test_malformed_catalog_retains_secret(self):
        self.session.get.return_value.json.return_value = {'error':'bad'}
        with self.assertRaises(AuthorizationFailure):
            restore_token('Atzr|example',1,self.db,self.session)
        self.db.save_seller_credentials.assert_not_called()

    def test_invalid_token_never_sent(self):
        with self.assertRaises(AuthorizationFailure):
            restore_token('invalid',1,self.db,self.session)
        self.session.post.assert_not_called()


if __name__ == '__main__':
    unittest.main()
