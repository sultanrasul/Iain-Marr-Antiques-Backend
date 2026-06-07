import csv

from services.integrations.integrations import get_sheets_service
sheetsService = get_sheets_service()
sheetsService.add_order_ids()

# from services.integrations.database_service import DatabaseService
# databaseService = DatabaseService("database.sqlite")

# items that have duplicate SKU NO: {'3-329a', '3-363', 'IMA 2-114', '3-364', '3-528', 'IMA 2-275', '3-365', '3-370', '3-375a', '3-376a', '3-372', '2-664'}

import csv

# from services.system import SystemService
# print("Last modified:", sheetsService.get_last_modified())

# sheetsService.convert_old_date_format()

# systemService = SystemService()
# print(f"OUTPUT OF IMPORT: {systemService.import_google_sheets_data()} ")

# products = sheetsService.get_stock()
# errors = databaseService.import_products_to_db(products=products)
# print(errors)

# print()

# sold_products = sheetsService.get_sold_items()
# errors = databaseService.import_sold_products_to_db(sold_products=sold_products)
# print(errors)

# databaseService.conn.close()