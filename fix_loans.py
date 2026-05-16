from main.models import LoanProduct

LoanProduct.objects.all().delete()

products = [
    ('NCL', 'NCL - Non-Collateralized Loan', 20.00, 12, 2000, 50000, True),
    ('APCP', 'APCP - Agricultural Production Credit Program', 15.00, 12, 2000, 50000, True),
    ('SALARY', 'SALARY - Salary Loan', 8.00, 12, 1500, 50000, False),
    ('COLLATERAL', 'COLLATERAL - Secured Loan', 20.00, 12, 2000, 100000, True),
    ('PROVIDENTIAL', 'PROVIDENTIAL - Providential Loan', 16.00, 12, 2000, 50000, True),
    ('B2B', 'B2B - Back to Back Loan', 20.00, 12, 5000, 100000, True),
    ('TRADE', 'TRADE - Trade Loan', 18.00, 1, 2000, 30000, True),
]

for lt, dn, rate, term, min_a, max_a, req in products:
    obj, created = LoanProduct.objects.get_or_create(
        loan_type=lt,
        defaults={
            'name': lt,
            'display_name': dn,
            'interest_rate': rate,
            'term_months': term,
            'min_amount': min_a,
            'max_amount': max_a,
            'requires_comaker': req,
        }
    )
    print(f'Created {lt}')

print(f'Done! Total: {LoanProduct.objects.count()}')
