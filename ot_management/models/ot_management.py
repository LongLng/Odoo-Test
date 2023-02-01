from odoo import fields, api, models
from odoo import tools, _
from odoo.exceptions import ValidationError, AccessError

from odoo.fields import Date, Datetime
from datetime import datetime, tzinfo
from dateutil import tz
import holidays

import pytz


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
    additional_hours = fields.Float(string='Total OT', readonly=True, compute='addition_all_ot')
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'To Approve'), ('pm_approved', 'PM Approved'),
         ('dl_approved', 'DL Approved'), ('refused', 'Refused')], default='draft', readonly=True)
    ot_registration_line_ids = fields.One2many('ot.registration.line', 'ot_registration_line_id',
                                               string='OT Registration Lines')
    group_user = fields.Char(compute='get_user_group')

    def get_user_group(self):
        for rec in self:
            if self.env.user.has_group('ot_management.group_ot_dl'):
                print('dl')
                rec.group_user = 'dl'
            elif self.env.user.has_group('ot_management.group_ot_pm'):
                print('pm')
                rec.group_user = 'pm'
            elif self.env.user.has_group('ot_management.group_ot_employee'):
                print('employee')
                rec.group_user = 'employee'

    @api.depends('ot_registration_line_ids')
    def addition_all_ot(self):
        for rec in self:
            rec.additional_hours = sum(rec.ot_registration_line_ids.mapped('additional_hours'))
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

    def button_employ_submit(self):
        for rec in self:
            if rec.env.user.has_group('ot_management.group_ot_employee'):
                rec.state = 'to_approve'

    def button_pm_approve(self):
        for rec in self:
            if rec.env.user.has_group('ot_management.group_ot_pm'):
                rec.state = 'pm_approved'

    def button_dl_approve(self):
        for rec in self:
            if rec.env.user.has_group('ot_management.group_ot_dl'):
                rec.state = 'dl_approved'

    def button_refuse(self):
        for rec in self:
            if rec.env.user.has_group('ot_management.group_ot_pm') and rec.state == 'pm_approved':
                rec.state = 'refused'
            elif rec.env.user.has_group('ot_management.group_ot_dl') and rec.state == 'dl_approved':
                rec.state = 'refused'

    def button_draft(self):
        for rec in self:
            if rec.env.user.has_group('ot_management.group_ot_employee') and rec.state == 'refused':
                rec.state = 'draft'


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
                                 ('unknown', 'Không thể xác định')], string='OT Category', store=True,
                                compute='get_category_OT')
    is_wfh = fields.Boolean(string='WFH')
    is_intern = fields.Boolean(string='Is intern', default=False)
    additional_hours = fields.Float(string='OT hours', readonly=True, store=True, compute='addition_ot_hours')
    job_taken = fields.Char(string='Job Taken', default='N/A')
    late_approved = fields.Boolean(string='Late Approved', readonly=True)
    hr_notes = fields.Text(string='HR Notes', readonly=True)
    attendance_notes = fields.Text(string='Attendance Notes', readonly=True)
    notes = fields.Char(string='Warning', default='Exceed OT plan', readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'To Approve'), ('pm_approved', 'PM Approved'),
         ('dl_approved', 'DL Approved'), ('refused', 'Refused')], related='ot_registration_line_id.state',
        default='draft',
        readonly=True, store=True)

    @api.depends('date_from', 'date_to')
    def addition_ot_hours(self):
        for rec in self:
            ot_hours = (rec.date_to - rec.date_from).total_seconds()
            rec.additional_hours = ot_hours / 3600
            print('ot_hours', ot_hours)

    def set_utc_to_local(self, utc_time, user_timezone):
        format = "%H:%M:%S"
        dt_utc = datetime.strptime(utc_time, format)
        dt_utc = dt_utc.replace(tzinfo=pytz.UTC)
        dt_local = dt_utc.astimezone(user_timezone)
        local_time_str = dt_local.strftime(format)
        return local_time_str

    def check_date(self, date_from, date_to):
        vn_holidays = holidays.VN()
        if date_from in vn_holidays and date_to in vn_holidays:
            print("holidays")
            return 'Holiday'
        if date_from.weekday() == 5:
            print(date_from.weekday())
            return 'Saturday'
        if date_from.weekday() == 6:
            print(date_from.weekday())
            return 'Sunday'
        else:
            print('unknown')
            return 'unknown'

    def check_time(self, time_from, time_to):
        format = "%H:%M:%S"
        print('Time-from:', datetime.strptime(time_from, format))
        print('Time-to:', datetime.strptime(time_to, format))
        if datetime.strptime(time_from, format) < datetime.strptime(time_to, format):

            if datetime.strptime('06:00:00', format) <= datetime.strptime(time_from, format) and datetime.strptime(
                    '20:30:00', format) >= datetime.strptime(time_to, format):
                return 'Day'
                print('Day')
            else:
                return 'Night'
                print('Night')
        else:
            return 'unknown'

    @api.depends('date_from', 'date_to')
    def get_category_OT(self):
        for rec in self:
            user_timezone = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
            # date_timezone = pytz.utc.localize(rec.date_from).astimezone(user_timezone)
            time_from = rec.date_from.strftime("%H:%M:%S")
            time_to = rec.date_to.strftime("%H:%M:%S")
            date_cate = self.check_date(rec.date_from, rec.date_to)
            time_cate = self.check_time(self.set_utc_to_local(time_from, user_timezone),
                                        self.set_utc_to_local(time_to, user_timezone))
            if date_cate == 'Holiday':
                if time_cate == 'Day':
                    rec.category = 'holiday'
                elif time_cate == 'Night':
                    rec.category = 'holiday_day_night'
                else:
                    rec.category = 'unknown'
            elif date_cate == 'Saturday':
                if time_cate == 'Day':
                    rec.category = 'saturday'
                elif time_cate == 'Night':
                    rec.category = 'weekend_day_night'
                else:
                    rec.category = 'unknown'
            elif date_cate == 'Sunday':
                if time_cate == 'Day':
                    rec.category = 'sunday'
                elif time_cate == 'Night':
                    rec.category = 'weekend_day_night'
                else:
                    rec.category = 'unknown'

            else:
                if time_cate == 'Day':
                    rec.category = 'normal_day'
                elif time_cate == 'Night':
                    rec.category = 'normal_day_night'
                else:
                    rec.category = 'unknown'

            print('a', time_from)
            print('Date', rec.date_from.strftime("%m/%d/%Y"))
