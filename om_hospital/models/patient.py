from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, AccessError


class HospitalPatient(models.Model):
    def get_appointment_count(self):
        count = self.env['hospital.appointment'].search_count([('patient_id', '=', self.id)])
        self.appointment_count = count

    _name = 'hospital.patient'
    _description = 'Patient Record'
    _rec_name = 'name_seq'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    patient_name = fields.Char(string='Name', required=True)
    patient_age = fields.Integer(string='Age', track_visibility='always')
    notes = fields.Text(string='Notes')
    image = fields.Binary(string='Image')
    name = fields.Char(string='Test')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], default='male', string='Gender')
    age_group = fields.Selection([('major', 'Major'), ('minor', 'Minor')], string='Age Group', compute='set_age_group')
    name_seq = fields.Char(string='Patient ID', required=True, copy=False, readonly=True, index=True,
                           default=lambda self: _('New'))
    appointment_count = fields.Integer(string='Appointment', compute='get_appointment_count')

    # Tao 1 bảng trong db Constraints sau đó so sánh dữ liệu với bảng đó, không bị xóa
    # _sql_constraints = [('patient_name', 'unique(patient_name)', 'Patient name must be unique')]

    @api.constrains('patient_age')
    def check_age(self):
        for rec in self:
            if rec.patient_age <= 5:
                raise ValidationError(_('The Age Must be Greater than 5'))

    @api.multi
    def open_patient_appointments(self):
        return {
            'name': _('Appointments'),
            'domain': [('patient_id', '=', self.id)],
            'res_model': 'hospital.appointment',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    # Store = True  thì chỉ tính toán khi truờng được gán thay đổi
    # compute thì tự động cập nhật dữ liệu từ db và trường được gán compute thì được chuyển thành readonly store = False
    @api.depends('patient_age')
    def set_age_group(self):
        for rec in self:
            if rec.patient_age:
                if rec.patient_age < 18:
                    rec.age_group = 'minor'
                else:
                    rec.age_group = 'major'

    # onchange chỉ bắt sự kiện trên view có store mặc định bằng True

    # @api.onchange('patient_age')
    # def _set_age_group(self):
    #     if self.patient_age:
    #         if self.patient_age < 18:
    #             self.age_group = 'minor'
    #         else:
    #             self.age_group = 'major'

    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('hospital.patient.sequence') or _('New')
        result = super(HospitalPatient, self).create(vals)
        return result
