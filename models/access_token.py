import hashlib
import logging
import os
from datetime import datetime, timedelta

from odoo import api, fields, models, http
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, FILETYPE_BASE64_MAGICWORD

_logger = logging.getLogger(__name__)


# we can make the expiry as a value taken from the
# token_expiry_date_in = "api_project.access_token_token_expiry_date_in"
# print("token_expiry_date_in :", token_expiry_date_in)



import requests
import base64
from odoo import models, fields, api


def generate_token(length=40, prefix="ac"):
    # we can agree here how we can manage the token?
    rbytes = os.urandom(length)
    return "{}_{}".format(prefix, str(hashlib.sha1(rbytes).hexdigest()))







class ProductImage(models.Model):
    _inherit = 'product.template'

    image_url = fields.Char(string='Image URL')

    @api.onchange('image_url')
    def _onchange_image_url(self):
        """ function to load image from URL """
        image = False
        if self.image_url:
            image = base64.b64encode(requests.get(self.image_url).content)
        self.image_1920 = image


class ProductVariantImage(models.Model):
    _inherit = 'product.product'

    image_url = fields.Char(string='Image URL')

    @api.onchange('image_url')
    def _onchange_image_url(self):
        """ function to load image from URL in product variant"""
        image = False
        if self.image_url:
            image = base64.b64encode(requests.get(self.image_url).content)
        self.image_1920 = image

#
# class Http(models.AbstractModel):
#     _inherit = 'ir.http'

    # def session_info(self):
    #     uid = request.session.uid
        #cookies = request.httprequest.cookies
        #access_token = request.env["api.access_token"].find_or_create_token(user_id=uid, create=True)
        # res = super(Http, self).session_info()
        # res['session_id'] = request.session.sid
        # #if not res.get('access_token'):
            #res['access_token'] = access_token
        #     if not res.get('X-Openerp-Session-Id'):
        #     res['X-Openerp-Session-Id'] = request.session.sid
        # print("====", request.httprequest.cookies)
        #
        # return res


class APIAccessToken(models.Model):
    _name = "api.access_token"
    _description = "API Access Token"

    token = fields.Char("Access Token", required=True)
    user_id = fields.Many2one("res.users", string="User", required=True)
    token_expiry_date = fields.Datetime(string="Token Expiry Date", required=True)
    scope = fields.Char(string="Scope")

    def find_or_create_token(self, user_id=None, create=False):
        if not user_id:
            user_id = self.env.user.id

        access_token = self.env["api.access_token"].sudo().search([("user_id", "=", user_id)], order="id DESC", limit=1)
        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():
                access_token = None
        if not access_token and create:
            token_expiry_date = datetime.now() + timedelta(days=1)
            vals = {
                "user_id": user_id,
                "scope": "userinfo",
                "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "token": generate_token(),
            }
            access_token = self.env["api.access_token"].sudo().create(vals)
        if not access_token:
            return None
        return access_token.token

    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.

        :param scopes: An iterable containing the scopes to check or None
        """
        self.ensure_one()
        return not self.has_expired() and self._allow_scopes(scopes)

    def has_expired(self):
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.token_expiry_date)

    def _allow_scopes(self, scopes):
        self.ensure_one()
        if not scopes:
            return True

        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)


class Users(models.Model):
    _inherit = "res.users"

    def sum_numbers(self, x, y):
        return x + y

    token_ids = fields.One2many("api.access_token", "user_id", string="Access Tokens")


# class SaleOrder(models.Model):
#     _inherit = "sale.order"
#
#
# class SaleOrderLine(models.Model):
#     _inherit = "sale.order.line"
