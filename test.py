import csv

from services.integrations.sheets_service import SheetsService
sheetsService = SheetsService()

from services.integrations.database_service import DatabaseService
databaseService = DatabaseService("database.sqlite")

# items that have duplicate SKU NO: {'3-329a', '3-363', 'IMA 2-114', '3-364', '3-528', 'IMA 2-275', '3-365', '3-370', '3-375a', '3-376a', '3-372', '2-664'}

import csv

products = sheetsService.get_stock()
errors = databaseService.import_products_to_db(products=products)
print(errors)

print()

sold_products = sheetsService.get_sold_items()
errors = databaseService.import_sold_products_to_db(sold_products=sold_products)
print(errors)

databaseService.conn.close()