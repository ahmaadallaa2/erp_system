STANDARD_CHART_OF_ACCOUNTS = [
    {
        "code": "1000",
        "name": "Assets",
        "account_type": "asset",
        "normal_balance": "debit",
        "is_postable": False,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": None,
    },
    {
        "code": "1001",
        "name": "Bank",
        "account_type": "asset",
        "normal_balance": "debit",
        "is_postable": True,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": "1000",
    },
    {
        "code": "1002",
        "name": "Cash",
        "account_type": "asset",
        "normal_balance": "debit",
        "is_postable": True,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": "1000",
    },
    {
        "code": "1003",
        "name": "Accounts Receivable",
        "account_type": "asset",
        "normal_balance": "debit",
        "is_postable": True,
        "is_active": True,
        "allow_reconciliation": True,
        "parent_code": "1000",
    },
    {
        "code": "1004",
        "name": "Inventory",
        "account_type": "asset",
        "normal_balance": "debit",
        "is_postable": True,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": "1000",
    },
    {
        "code": "2000",
        "name": "Liabilities",
        "account_type": "liability",
        "normal_balance": "credit",
        "is_postable": False,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": None,
    },
    {
        "code": "2001",
        "name": "Accounts Payable",
        "account_type": "liability",
        "normal_balance": "credit",
        "is_postable": True,
        "is_active": True,
        "allow_reconciliation": True,
        "parent_code": "2000",
    },
    {
        "code": "3000",
        "name": "Equity",
        "account_type": "equity",
        "normal_balance": "credit",
        "is_postable": False,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": None,
    },
    {
        "code": "3001",
        "name": "Owner Capital",
        "account_type": "equity",
        "normal_balance": "credit",
        "is_postable": True,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": "3000",
    },
    {
        "code": "4000",
        "name": "Income",
        "account_type": "income",
        "normal_balance": "credit",
        "is_postable": False,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": None,
    },
    {
        "code": "4001",
        "name": "Sales Revenue",
        "account_type": "income",
        "normal_balance": "credit",
        "is_postable": True,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": "4000",
    },
    {
        "code": "5000",
        "name": "Expenses",
        "account_type": "expense",
        "normal_balance": "debit",
        "is_postable": False,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": None,
    },
    {
        "code": "5001",
        "name": "Cost of Goods Sold",
        "account_type": "expense",
        "normal_balance": "debit",
        "is_postable": True,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": "5000",
    },
    {
        "code": "5002",
        "name": "Operating Expenses",
        "account_type": "expense",
        "normal_balance": "debit",
        "is_postable": True,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": "5000",
    },
    {
        "code": "5003",
        "name": "Purchase Expenses",
        "account_type": "expense",
        "normal_balance": "debit",
        "is_postable": True,
        "is_active": True,
        "allow_reconciliation": False,
        "parent_code": "5000",
    },
]


def seed_standard_chart_of_accounts(company, account_model=None):
    if account_model is None:
        from apps.accounting.models.account import Account

        account_model = Account

    accounts_by_code = {}

    for account_data in STANDARD_CHART_OF_ACCOUNTS:
        if account_data["parent_code"] is None:
            accounts_by_code[account_data["code"]] = _ensure_account(
                company=company,
                account_model=account_model,
                account_data=account_data,
                parent=None,
            )

    for account_data in STANDARD_CHART_OF_ACCOUNTS:
        parent_code = account_data["parent_code"]

        if parent_code is None:
            continue

        parent = accounts_by_code[parent_code]
        accounts_by_code[account_data["code"]] = _ensure_account(
            company=company,
            account_model=account_model,
            account_data=account_data,
            parent=parent,
        )

    return accounts_by_code


def _ensure_account(company, account_model, account_data, parent):
    account = (
        account_model.objects.filter(
            company=company,
            code=account_data["code"],
            is_deleted=False,
        )
        .order_by("id")
        .first()
    )

    defaults = {
        "name": account_data["name"],
        "account_type": account_data["account_type"],
        "normal_balance": account_data["normal_balance"],
        "is_postable": account_data["is_postable"],
        "is_active": account_data["is_active"],
        "allow_reconciliation": account_data["allow_reconciliation"],
        "parent": parent,
    }

    if account is None:
        return account_model.objects.create(
            company=company,
            code=account_data["code"],
            **defaults,
        )

    changed_fields = []
    for field, value in defaults.items():
        if field == "name":
            continue

        if getattr(account, field) != value:
            setattr(account, field, value)
            changed_fields.append(field)

    if changed_fields:
        account.save(update_fields=changed_fields)

    return account
