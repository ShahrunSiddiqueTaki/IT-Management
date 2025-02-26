# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields, api, _
from odoo.exceptions import MissingError, ValidationError, UserError
from dateutil.relativedelta import relativedelta


class ItRequisition(models.Model):
    _name = 'it.requisition'
    _description = 'IT Requisition'
    _inherit = ['mail.thread']
    _order = 'id desc'

    state = fields.Selection(selection=[('draft', 'Draft'), ('approved', 'Approved'), ('cancelled', 'Cancelled'), ('closed', 'Closed')], default='draft')

    name = fields.Char(string='Name', default='New', tracking=True, readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env.company, tracking=True)
    supplier_id = fields.Many2one(comodel_name='res.partner', string='Supplier', tracking=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', tracking=True)
    department_id = fields.Many2one(comodel_name='hr.department', string='Department', tracking=True)
    description = fields.Text(string='Description', tracking=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.today(), tracking=True, readonly=True)
    date_required = fields.Date(string='Date Required', default=lambda self: fields.Date.today()+relativedelta(days=7), tracking=True)
    prepared_by_id = fields.Many2one(comodel_name='res.users', string='Prepared By', default=lambda self: self.env.uid, tracking=True, readonly=True)
    line_ids = fields.One2many(comodel_name='it.requisition.line', inverse_name='requisition_id', string='Requisition Lines')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
    grand_total = fields.Monetary(string="Grand Total", store=True, compute='_compute_grand_total', tracking=True)
    quantity_total = fields.Integer(string="Quantity Total", compute='_compute_quantity_total')

    @api.depends('line_ids.subtotal')
    def _compute_grand_total(self):
        for rec in self:
            rec.grand_total = sum(line.subtotal for line in rec.line_ids)

    @api.depends('line_ids.quantity')
    def _compute_quantity_total(self):
        for rec in self:
            rec.quantity_total = sum(line.quantity for line in rec.line_ids)

    def _fields_validations(self):
        required_fields = [
            ('supplier_id', "Supplier is Missing"),
            ('employee_id', "Employee is Missing"),
            ('company_id', "Company is Missing"),
            ('date_required', "Required Date is Missing"),
            ('request_date', "Request Date is Missing"),
            ('line_ids', "Requisition Lines is Missing")
        ]

        for rec in self:
            for field, error_msg in required_fields:
                if not getattr(rec, field):
                    raise MissingError(error_msg)

            for line in rec.line_ids:
                if line.quantity <= 0:
                    raise ValidationError("Invalid Product Quantity")
                if line.unit_price <= 0:
                    raise ValidationError("Invalid Product Unit Price")

            if rec.date_required < rec.request_date:
                raise ValidationError("Invalid Required Date")

    def action_approve(self):
        for rec in self:
            rec._fields_validations()
            if rec.state == 'draft':
                rec.state = 'approved'

    def action_cancel(self):
        for rec in self:
            rec._fields_validations()
            rec.state = 'cancelled'

    def action_close(self):
        for rec in self:
            rec._fields_validations()
            if rec.state == 'approved':
                rec.state = 'closed'

    def action_amendment(self):
        for rec in self:
            rec._fields_validations()
            if rec.state == 'approved':
                rec.state = 'draft'


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('it.requisition.seq') or _('New')
        return super().create(vals_list)




class ItRequisitionLine(models.Model):
    _name = 'it.requisition.line'
    _description = 'IT Requisition Line'
    _inherit = ['mail.thread']

    requisition_id = fields.Many2one(comodel_name='it.requisition', string='Requisition', required=True, tracking=True)
    currency_id = fields.Many2one(related='requisition_id.currency_id')
    sequence = fields.Integer(string='Sequence', tracking=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Product', tracking=True)
    quantity = fields.Float(string='Quantity', default=1.0, tracking=True)
    unit_price = fields.Monetary(string='Unit Price', tracking=True)
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True, tracking=True)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price