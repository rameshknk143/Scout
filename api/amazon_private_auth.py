"""Validate private-app self-authorization before replacing an encrypted token."""
import os
import requests


class AuthorizationFailure(Exception):
    pass


def restore_token(token, user_id, db, session=requests):
    if not isinstance(token, str) or not token.startswith('Atzr|') or len(token) > 16384:
        raise AuthorizationFailure('A valid Amazon self-authorization refresh token is required.')
    credentials = db.get_seller_credentials(user_id)
    if len(credentials) != 1:
        raise AuthorizationFailure('Exactly one existing seller connection is required; no account was changed.')
    account = credentials[0]
    marketplace = account['marketplace_id']
    if marketplace != 'A21TJRUUN4KGV':
        raise AuthorizationFailure('This recovery path is restricted to the existing India connection.')
    client_id, secret = os.getenv('LWA_CLIENT_ID'), os.getenv('LWA_CLIENT_SECRET')
    if not client_id or not secret:
        raise AuthorizationFailure('Amazon application credentials are missing on the server.')
    try:
        response = session.post('https://api.amazon.com/auth/o2/token', data={
            'grant_type': 'refresh_token', 'refresh_token': token,
            'client_id': client_id, 'client_secret': secret}, timeout=(10, 40))
        if response.status_code != 200:
            raise AuthorizationFailure(f'Amazon token exchange denied (HTTP {response.status_code}); existing connection retained.')
        access = response.json().get('access_token')
        if not isinstance(access, str) or not access:
            raise AuthorizationFailure('Amazon returned no access token; existing connection retained.')
        catalog = session.get('https://sellingpartnerapi-eu.amazon.com/catalog/2022-04-01/items',
            headers={'x-amz-access-token': access}, params={
                'marketplaceIds': marketplace, 'keywords': 'phone case',
                'pageSize': 1, 'includedData': 'summaries'}, timeout=(10, 40))
        if catalog.status_code != 200:
            # One read-only control request distinguishes catalog-specific denial
            # from a broader SP-API grant/account denial. Never expose raw bodies.
            seller = session.get('https://sellingpartnerapi-eu.amazon.com/sellers/v1/marketplaceParticipations',
                headers={'x-amz-access-token': access}, timeout=(10, 25))
            raise AuthorizationFailure(f'Amazon login exchange succeeded; catalog HTTP {catalog.status_code}; seller-access HTTP {seller.status_code}. Existing connection retained.')
        result = catalog.json()
        if not isinstance(result, dict) or not isinstance(result.get('items'), list):
            raise AuthorizationFailure('Invalid catalog response; existing connection retained.')
    except (requests.RequestException, ValueError, TypeError):
        raise AuthorizationFailure('Amazon connection failed or returned invalid data; existing connection retained.') from None
    # All writes occur only after actual catalog authorization succeeds.
    db.save_seller_credentials(account['selling_partner_id'], token, user_id, marketplace)
    return {'ok': True, 'catalog_access': True, 'sample_items': len(result['items'])}

