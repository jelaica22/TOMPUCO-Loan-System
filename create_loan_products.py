from main.models import LoanProduct

# Delete existing products to start fresh
LoanProduct.objects.all().delete()

# Create all loan products with lower amounts
products = [
    {
        'loan_type': 'NCL',
        'name': 'NCL',
        'display_name': 'NCL - Non-Collateralized Loan',
        'interest_rate': 20.00,
        'term_months': 12,
        'min_amount': 2000,
        'max_amount': 50000,
        'requires_comaker': True,
        'description': 'Non-Collateralized Loan. 20% per annum, 360 days term, requires co-maker.'
    },
    {
        'loan_type': 'APCP',
        'name': 'APCP',
        'display_name': 'APCP - Agricultural Production Credit Program',
        'interest_rate': 15.00,
        'term_months': 12,
        'min_amount': 2000,
        'max_amount': 50000,
        'requires_comaker': True,
        'description': 'Agricultural Production Credit Program. 15% per annum, 360 days term.'
    },
    {
        'loan_type': 'SALARY',
        'name': 'SALARY',
        'display_name': 'SALARY - Salary Loan',
        'interest_rate': 8.00,
        'term_months': 12,
        'min_amount': 1500,
        'max_amount': 50000,
        'requires_comaker': False,
        'description': 'Salary loan for employees. 8% per annum, 360 days term, no co-maker required.'
    },
    {
        'loan_type': 'COLLATERAL',
        'name': 'COLLATERAL',
        'display_name': 'COLLATERAL - Secured Loan',
        'interest_rate': 20.00,
        'term_months': 12,
        'min_amount': 2000,
        'max_amount': 100000,
        'requires_comaker': True,
        'description': 'Collateralized Loan. 20% per annum, 360 days term, requires collateral.'
    },
    {
        'loan_type': 'PROVIDENTIAL',
        'name': 'PROVIDENTIAL',
        'display_name': 'PROVIDENTIAL - Providential Loan',
        'interest_rate': 16.00,
        'term_months': 12,
        'min_amount': 2000,
        'max_amount': 50000,
        'requires_comaker': True,
        'description': 'Providential loan. 16% per annum, 360 days term.'
    },
    {
        'loan_type': 'B2B',
        'name': 'B2B',
        'display_name': 'B2B - Back to Back Loan',
        'interest_rate': 20.00,
        'term_months': 12,
        'min_amount': 5000,
        'max_amount': 100000,
        'requires_comaker': True,
        'description': 'Back to Back loan. 20% per annum, 360 days term.'
    },
    {
        'loan_type': 'TRADE',
        'name': 'TRADE',
        'display_name': 'TRADE - Trade Loan',
        'interest_rate': 18.00,
        'term_months': 1,
        'min_amount': 2000,
        'max_amount': 30000,
        'requires_comaker': True,
        'description': 'Trade loan (Receivables). 1.5% per month, 30 days term only.'
    },
]

for product_data in products:
    product, created = LoanProduct.objects.get_or_create(
        loan_type=product_data['loan_type'],
        defaults={
            'name': product_data['name'],
            'display_name': product_data['display_name'],
            'interest_rate': product_data['interest_rate'],
            'term_months': product_data['term_months'],
            'min_amount': product_data['min_amount'],
            'max_amount': product_data['max_amount'],
            'requires_comaker': product_data['requires_comaker'],
            'description': product_data['description'],
        }
    )
    if created:
        print(f'✓ Created {product_data["loan_type"]}')
    else:
        print(f'○ {product_data["loan_type"]} already exists')

print()
print('=' * 50)
print(f'Total loan products: {LoanProduct.objects.count()}')
print('=' * 50)

print()
print('📋 Updated Loan Products:')
for product in LoanProduct.objects.all():
    co_maker = 'Required' if product.requires_comaker else 'Optional'
    print()
    print(f'  • {product.loan_type}: {product.display_name}')
    print(f'    - Interest: {product.interest_rate}% p.a.')
    print(f'    - Term: {product.term_months} month(s)')
    print(f'    - Amount: ₱{product.min_amount:,.0f} - ₱{product.max_amount:,.0f}')
    print(f'    - Co-maker: {co_maker}')
