from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo import http, _
import werkzeug


class OTRegistration(http.Controller):
    @http.route('/ot_management/ot_registration/<int:ot_id>', type='http', auth='user')
    def ot_registration(self, ot_id, **post):
        link = f'/web#id={ot_id}&action=344&model=ot.registration&view_type=form&menu_id=251'
        return werkzeug.redirect(link)
