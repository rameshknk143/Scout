"""List values live in snapshots; detailed/custom attributes retain field provenance."""
import os


def requires_field_ledger(row):
    if os.environ.get('SCOUT_LIST_FIELD_LEDGER_ENABLED', 'true').lower() == 'true':
        return True
    # Never suppress structured specifications, inferred attributes or sources
    # whose values are not fully represented by the existing list columns.
    return (row.get('list_type') not in {'bestsellers', 'new-releases'}
            or bool(row.get('attribute_observations')))
