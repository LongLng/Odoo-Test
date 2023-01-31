from odoo import fields, api, models
from odoo import tools, _
from odoo.exceptions import ValidationError, AccessError


class OTRegistration(models.Model):
    _name = 'ot.registration'
    _description = 'OT Registration'
    _rec_name = 'project_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    project_id = fields.Many2one('project.project', string='Project')
    manager_id = fields.Many2one('hr.employee', string='Approver', compute='get_default_approver', store=True,
                                 readonly=False, required=True)
    ot_month = fields.Date(string='OT Month', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True,
                                  default=lambda self: self._get_default_employee())
    dl_manager_id = fields.Many2one('hr.employee', string='Department lead', readonly=True,
                                    default=lambda self: self.get_default_department_leader())
    create_date = fields.Datetime(string='Created Date', readonly=True)
    additional_hours = fields.Float(string='Total OT', readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'To Approve'), ('pm_approved', 'PM Approve'),
         ('dl_approved', 'DL Approved'), ('refused', 'Refused')], default='draft', readonly=True)
    ot_registration_line_ids = fields.One2many('ot.registration.line', 'ot_registration_line_id',
                                               string='OT Registration Lines')

    # _sql_constraints = [('ot_registration', 'unique(project_id)', 'Project must be unique')]
    # @api.constrains('manager_id')
    # def _check_project_id(self):
    #     for rec in self:
    #         manager_id = self.env['ot.registration'].search(['manager_id', '=', rec.manager_id])
    #         if manager_id:
    #             raise ValidationError(_('You cannot create a recursive hierarchy.'))
    @api.depends('project_id')
    def get_default_approver(self):
        for rec in self:
            rec.manager_id = self.env['hr.employee'].search([('user_id.id', '=', rec.project_id.user_id.id)], limit=1)

    def _get_default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self._uid)], limit=1)

    def get_default_department_leader(self):
        pass

    def action_submit(self):
        print('Do U want to submit')


class OTRegistrationLine(models.Model):
    _name = 'ot.registration.line'
    _description = 'OT Registration Line'

    ot_registration_line_id = fields.Many2one('ot.registration', string='OT Registration ID', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', related='ot_registration_line_id.employee_id', store=True)
    project_id = fields.Many2one('project.project', related='ot_registration_line_id.project_id', store=True)
    date_from = fields.Datetime(string='From', default=fields.datetime.now(), required=True)
    date_to = fields.Datetime(string='To', default=fields.datetime.now(), required=True)
    category = fields.Selection([('normal_day', 'Ngày bình thường'),
                                 ('normal_day_morning', 'OT ban ngày (6h-8h30)'),
                                 ('normal_day_night', 'Ngày bình thường - Ban đêm'),
                                 ('saturday', 'Thứ 7'),
                                 ('sunday', 'Chủ nhật'),
                                 ('weekend_day_night', 'Ngày cuối tuần - Ban đêm'),
                                 ('holiday', 'Ngày lễ'),
                                 ('holiday_day_night', 'Ngày lễ - Ban đêm'),
                                 ('compensatory_normal', 'Bù ngày lễ vào ngày thường'),
                                 ('compensatory_night', 'Bù ngày lễ vào ban đêm'),
                                 ('unknown', 'Không thể xác định')], string='OT Category', store=True)
    is_wfh = fields.Boolean(string='WFH')
    is_intern = fields.Boolean(string='Is intern', default=False)
    additional_hours = fields.Float(string='Total OT', readonly=True)
    job_taken = fields.Char(string='Job Taken', default='N/A')
    late_approved = fields.Boolean(string='Late Approved', readonly=True)
    hr_notes = fields.Text(string='HR Notes', readonly=True)
    attendance_notes = fields.Text(string='Attendance Notes', readonly=True)
    notes = fields.Char(string='Warning', default='Exceed OT plan', readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'To Approve'), ('pm_approved', 'PM Approve'),
         ('dl_approved', 'DL Approved'), ('refused', 'Refused')], related='ot_registration_line_id.state',
        default='draft',
        readonly=True, store=True)
