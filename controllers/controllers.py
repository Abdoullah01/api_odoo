# -*- coding: utf-8 -*-


from odoo import http, exceptions
from odoo.http import request
import werkzeug.wrappers
from odoo.addons.api_project.models.common import invalid_response, valid_response
from odoo.exceptions import AccessDenied, AccessError, UserError
from functools import wraps
import json
import logging

import werkzeug

from odoo import http, tools, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db, Home, SIGN_UP_REQUEST_PARAMS
import xmlrpc.client

_logger = logging.getLogger(__name__)


class AuthSignupHome(Home):
    @http.route('/web/signup', type='http', auth='public', csrf=False)
    def web_auth_signup(self, *args, **kw):
        res = super(AuthSignupHome, self).web_auth_signup(*args, **kw)
        return res


class AccessToken(http.Controller):
    @http.route('/api/create_users', type='json', methods=['POST'], auth="public", csrf=False)
    def create_users(self, **kw):
        values = {
            "login": kw.get("login"),
            "name": kw.get("name"),
            'email': kw.get("login"),
            "password": kw.get("password"),
            "lang": kw.get("lang")
        }
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang

        db, login, password = request.env['res.users'].sudo().signup(values)
        request.env.cr.commit()
        # user_portal = request.env['res.users'].with_context({'no_reset_password': True}).create({
        #     'name': kw.get("name"),
        #     'login': kw.get("login"),
        #     'password': kw.get("password"),
        #     'email': kw.get("login"),
        #     'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])]
        # })

        data = {'id': request.env.user.id}
        return data

    @http.route('/api/create_ordered', type='json', methods=['POST'], auth="public", csrf=False, website=True)
    def create_ordered(self, **kw):
        order_line = kw.get('order_data')
        print("order_line  :", order_line)
        order_line_vals = []
        for product in order_line:
            order_line_vals.append((0, 0, {
                'product_id': product['product_id'],
                'product_uom_qty': product['quantity'],
                'price_unit': product['price']
            }))

        sale_order = request.env['sale.order'].sudo().create({
            'partner_id': request.env.user.partner_id.id,
            'order_line': order_line_vals
        })
        print("sale_order_line :", order_line_vals)
        sale_order.action_confirm()
        print("sale_order :", sale_order)
        data = {"status": 200, "response": sale_order.name, "message": "success"}
        return data

    @http.route(['/api/products', '/api/products/page/<int:page>'], type='http', methods=['GET'], auth="none", csrf=False, website=True)
    def get_product(self, page=0, ppg=False, **post):
        print("post    ", request.params)
        product_per_page = 10
        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        total = http.request.env['product.template'].sudo().search_count([])
        print("totol    ", total)
        products = http.request.env['product.template'].sudo().search([])
        print(len(products))
        pager = request.website.pager(url='/api/products', total=total, page=page, step=ppg, url_args=post)
        print("pager  ", pager)
        products = http.request.env['product.template'].sudo().search([], offset=pager['offset'], limit=ppg)
        products_list = []
        for product in products:
            if product.image_1920:
                vals = {
                    'id': product.id,
                    'name': product.name,
                    'list_price': product.list_price,
                    'description_sale': product.description_sale,
                    "category": [c.name for c in product.public_categ_ids],
                    "sub_category": [c.name for c in  product.public_categ_ids.child_id],
                    'image_1920': product.image_1920.decode('utf-8'),


                }
            products_list.append(vals)
            print("tailes     : ", len(products_list))
        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                products_list
            ),
        )

    @http.route('/api/products/<int:product_id>', type='http', methods=['GET'], auth="none", csrf=False)
    def get_product_by_id(self, product_id=None):
        # Récuperer les variants d'artcicle,
        products = http.request.env['product.product'].sudo().search([('product_tmpl_id', '=', product_id)])
        products_list = []
        for p in products:
            if p.image_1920:
                vals = {
                    'id': p.id,
                    'name': p.name,
                    'list_price': p.list_price,
                    'description_sale': p.description_sale,
                    "category": [c.name for c in p.public_categ_ids],
                    "sub_category": [c.name for c in  p.public_categ_ids.child_id],
                    'image_1920': p.image_1920.decode('utf-8')

                }
                products_list.append(vals)
                print("products_list    : ", len(products_list))
        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                products_list
            ),
        )

    @http.route('/api/categories', type='http', methods=['GET'], auth="none", csrf=False)
    def category(self):
        category = request.env['product.public.category'].sudo().search([])
        categories = []
        for c in category:
            if c.name in ('HOMME', 'FEMME', 'BÉBÉ', 'GARÇON', 'FILLE'):
                print("c ===", c)
                vals = {
                    "id": c.id,
                    "name": c.name,
                    "sub_category": [p.name for p in c.child_id],
                    "image_1920": c.image_1920.decode('utf-8') if c.image_1920 else False,
                    # "parent_id": [{'id': p.id, 'name': p.name} for p in c.parent_id],

                    # "parent_path": c.parent_path,
                    # "display_name": c.display_name,
                    # "product_tmpl_ids": [i.name for i in c.product_tmpl_ids],
                    # "parents_and_self": [i.id for i in c.parents_and_self]
                }
                categories.append(vals)
        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                categories
            ),
        )

    @http.route('/api/categories/<int:category_id>', type='http', methods=['GET'], auth="none", csrf=False)
    def get_by_product_category(self, category_id=None):

        # query = '''
        #         select * from product_public_category_product_template_rel where product_public_category_id in %(ids)s'''
        # cr = request._cr
        # cr.execute(query, {"ids": tuple(category.search([("id", "=", category_id)]).child_id.ids)})
        # data = cr.dictfetchall()
        # print('data', data)
        # prod = []
        # all_data = []
        # for ln in data:
        #     vals = {
        #         "categ_id": ln.get("product_public_category_id"),
        #         "categ_name": category.search([("id", "=", ln.get("product_public_category_id"))]).name,
        #         "parent_id": category_id,
        #     }
        #
        #     products = request.env['product.product'].sudo().search([
        #         ('product_tmpl_id', '=', ln.get("product_template_id"))])
        #     for p in products:
        #         if p.image_1920:
        #             val = {
        #                 'id': p.id,
        #                 'name': p.name,
        #                 'list_price': p.list_price,
        #                 'description_sale': p.description_sale,
        #                 'image_1920': p.image_1920.decode('utf-8')
        #
        #             }
        #         prod.append(val)
        #         print("prod   :", prod)
        #     vals.update(
        #         {"product": prod}
        #     )
        #     all_data.append(vals)
        #     print("prod   :", all_data)
        category = request.env['product.public.category'].sudo().search([('id', 'child_of', category_id)])
        #product_obj = request.env['product.product'].sudo().search([('public_categ_ids', '=', category_id)])
        product_category = []
        for cat in category:
            vals = {
                "id": cat.id,
                "name": cat.name,
                "product": [{
                    "id": p.name,
                    "name": p.name,
                    'list_price': p.list_price,
                    'description_sale': p.description_sale,
                    "category": [c.name for c in p.public_categ_ids],
                    "sub_category": [c.name for c in p.public_categ_ids.child_id],
                    'image_1920': p.image_1920.decode('utf-8')
                } for p in cat.product_tmpl_ids]
            }
            product_category.append(vals)


        # for product in product_obj:
        #     if product.image_1920:
        #         vals = {
        #             'id': product.id,
        #             'name': product.name,
        #             'list_price': product.list_price,
        #             'description_sale': product.description_sale,
        #             'image_1920': product.image_1920.decode('utf-8'),
        #
        #         }
        #         product_category.append(vals)

        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                product_category
            ),
        )

    @http.route('/products', type='json', auth='none', methods=['GET'], csrf=False)
    def test_api(self, **kw):
        print("session_id", request.session.sid)
        print("website      : ", request.env.user.lang)
        product_obj = http.request.env['product.template'].sudo().search([])
        # product_obj = http.request.env['product.product'].sudo().search([])
        # product_obj = http.request.env['product.template'].attribute_line_ids
        # for p in product_obj:
        #     if p.image_1920:
        #         print("Url : ", image_data_uri(p.image_1920))

        #     print("attribute_line_ids2 : ", p.attribute_line_ids.value_ids)
        # print("product_obj              :", product_obj.product_tmpl_id.name)
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        products_list = []
        for product in product_obj:
            image_url_1920 = base_url + '/web/image/product.product/' + str(product.id) + '/image_1920'
            if product.image_1920:
                print("product.public_categ_ids   ", len(product.public_categ_ids.child_id))
                vals = {
                    'id': product.id,
                    'name': product.name,
                    "public_categ_ids": [p.name for p in product.public_categ_ids],
                    "public_categ_id": [p.name for p in product.public_categ_ids.child_id],
                    'color': product.color,
                    'categ_id': product.categ_id,
                    # 'product_variant_ids': {
                    #     'image_variant_1920': [p.image_variant_1920 for p in product.product_variant_ids if p.image_variant_1920],
                    #     'product_template_variant_value_ids': [p.name for p in product.product_variant_ids.product_template_variant_value_ids]
                    #                         },
                    'is_product_variant': product.is_product_variant,
                    "attribute_line_ids.attribute_id": [p.attribute_id.name for p in product.attribute_line_ids],
                    'list_price': product.list_price,
                    'description': product.description,
                    'image_variant_1920': [p.image_variant_1920.decode('utf-8') for p in product.product_variant_ids if
                                           p.is_product_variant and p.image_variant_1920],
                    'image_1920': image_url_1920,
                }
                print("len   : ", len(vals['image_variant_1920']))
                products_list.append(vals)

        data = {"status": 200, "response": products_list, "message": "success"}
        return data
 # 'product_variant_ids': [{
                    #     'id': pv.id,
                    #     'name': pv.name,
                    #     'description_sale': pv.description_sale,
                    #     'lst_price': pv.lst_price,
                    #     'image_variant_1920': pv.image_1920.decode('utf-8')
                    #     if pv.image_1920 else False
                    #
                    # } for pv in product.product_variant_ids],
                    # 'attribute_line_ids': {
                    #     'attribute_id': [p.attribute_id.name for p in product.attribute_line_ids],
                    #     # 'value_ids': [p.value_ids for p in product.attribute_line_ids]
                    # },
                    # 'product_template_variant_value_ids': [p.id for p in product.product_template_variant_value_ids],