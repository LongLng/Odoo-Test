from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, AccessError


class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    def _get_default(self):
        return 'Fill to Registration Note'

    name = fields.Char(string='Appointment ID', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    patient_id = fields.Many2one('hospital.patient', string='Patient', required=True)
    patient_age = fields.Integer(string='Age', related='patient_id.patient_age', store=True)
    notes = fields.Text(string='Registration Note', default=_get_default)
    appointment_date = fields.Date(string='Date', required=True)

    # @api.depends('patient_id','patient_id.patient_age')
    # def set_age(self):
    #     for rec in self:
    #         if rec.patient_id and rec.patient_id.patient_age:
    #             rec.patient_age = rec.patient_id.patient_age

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hospital.appointment') or _('New')
        result = super(HospitalAppointment, self).create(vals)
        return result
