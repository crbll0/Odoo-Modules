
import logging
import pdb

from openerp.osv import osv, fields

_logger = logging.getLogger(__name__)


class ProductUpdate(osv.osv):
    _inherit = 'product.template'

    def update_product_categ(self):
        # pro = self.pool.get('product.template')
        prod_ids = self.search(cr, uid, [('purchase_ok','=', True)])
        products = self.browse(cr, uid, prod_ids)

        for num, product in enumerate(products):
        # print num
        # print product.categ_id.property_account_income_categ
        # print product.property_account_income
        # print product.property_account_income
        # print product.categ_id.property_account_income_categ
        # print product.id
        _logger.info('{} / {})'.format(num, len(products)))
        if product.categ_id.property_account_income_categ and not product.property_account_income:
            self.write(cr, uid, product.id,
                      {'property_account_income':product.categ_id.property_account_income_categ.id})

        if product.categ_id.property_account_expense_categ and not product.property_account_expense:

            self.write(cr, uid, product.id,
                      {'property_account_expense': product.categ_id.property_account_expense_categ.id})

        if product.categ_id.property_stock_account_input_categ and not product.property_stock_account_input:

            self.write(cr, uid, product.id,
                      {'property_stock_account_input': product.categ_id.property_stock_account_input_categ.id})

        _logger.info(product.id)