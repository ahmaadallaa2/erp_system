from apps.accounting.models.account import Account


def ensure_account(company, code, **fields):
    """
    Return the company's active account for `code` with `fields` applied.

    New companies already carry the standard chart of accounts, so fixtures
    must adjust the seeded row instead of inserting a duplicate code.
    """
    account = Account.objects.filter(
        company=company,
        code=code,
        is_deleted=False,
    ).first()

    if account is None:
        return Account.objects.create(company=company, code=code, **fields)

    for field, value in fields.items():
        setattr(account, field, value)
    account.save()
    return account
