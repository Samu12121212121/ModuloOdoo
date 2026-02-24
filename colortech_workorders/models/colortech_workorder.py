
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ColortechWorkorder(models.Model):
    """Orden de Trabajo principal.

    Registra cada dispositivo que entra al taller con su flujo completo:
    Recibido → En Proceso → Secado → Control de Calidad → Entregado.
    """
    _name = 'colortech.workorder'
    _description = 'Orden de Trabajo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_received desc, id desc'

    # ---- Identificación ----
    name = fields.Char(
        string='Nº Orden',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo',
    )

    # ---- Datos del cliente ----
    client_name = fields.Char(
        string='Nombre del Cliente',
        required=True,
        tracking=True,
    )
    client_phone = fields.Char(
        string='Teléfono',
    )
    client_email = fields.Char(
        string='Email',
    )

    # ---- Datos del dispositivo ----
    device_type_id = fields.Many2one(
        comodel_name='colortech.device.type',
        string='Tipo de Dispositivo',
        required=True,
        tracking=True,
    )
    device_brand = fields.Char(
        string='Marca',
        required=True,
    )
    device_model = fields.Char(
        string='Modelo',
        required=True,
    )
    device_serial = fields.Char(
        string='Nº Serie / IMEI',
    )
    device_condition = fields.Selection(
        selection=[
            ('bueno', 'Buen Estado'),
            ('normal', 'Estado Normal'),
            ('danado', 'Con Daños'),
            ('roto', 'Roto / Para Restaurar'),
        ],
        string='Estado del Dispositivo',
        default='normal',
    )
    device_notes = fields.Text(
        string='Observaciones del Dispositivo',
    )

    # ---- Asignación ----
    technician_name = fields.Char(
        string='Técnico Asignado',
        tracking=True,
    )
    priority = fields.Selection(
        selection=[
            ('0', 'Normal'),
            ('1', 'Urgente'),
            ('2', 'Muy Urgente'),
        ],
        string='Prioridad',
        default='0',
    )

    # ---- Fechas ----
    date_received = fields.Date(
        string='Fecha de Recepción',
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )
    date_promised = fields.Date(
        string='Fecha Prometida de Entrega',
    )
    date_delivered = fields.Date(
        string='Fecha de Entrega Real',
        tracking=True,
    )

    # ---- Líneas de servicio ----
    line_ids = fields.One2many(
        comodel_name='colortech.workorder.line',
        inverse_name='workorder_id',
        string='Servicios a Realizar',
        copy=True,
    )

    # ---- Estado (flujo de trabajo) ----
    state = fields.Selection(
        selection=[
            ('recibido', 'Recibido'),
            ('en_proceso', 'En Proceso'),
            ('secado', 'En Secado'),
            ('control', 'Control de Calidad'),
            ('terminado', 'Terminado'),
            ('entregado', 'Entregado'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado',
        default='recibido',
        required=True,
        tracking=True,
    )

    # ---- Campos computados ----
    total_cost = fields.Float(
        string='Coste Total (€)',
        compute='_compute_totals',
        digits=(10, 2),
        store=True,
    )
    total_hours = fields.Float(
        string='Horas Estimadas Totales',
        compute='_compute_totals',
        store=True,
    )
    service_count = fields.Integer(
        string='Nº Servicios',
        compute='_compute_totals',
        store=True,
    )

    notes = fields.Text(string='Notas Internas')
    active = fields.Boolean(string='Activo', default=True)

    # ---- Computed ----
    @api.depends('line_ids.subtotal', 'line_ids.estimated_hours')
    def _compute_totals(self):
        for rec in self:
            rec.total_cost = sum(rec.line_ids.mapped('subtotal'))
            rec.total_hours = sum(rec.line_ids.mapped('estimated_hours'))
            rec.service_count = len(rec.line_ids)

    # ---- Secuencia automática ----
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'colortech.workorder') or 'Nuevo'
        return super().create(vals_list)

    # ---- Acciones de estado (botones) ----
    def action_en_proceso(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(
                    'Añade al menos un servicio antes de iniciar.')
            rec.state = 'en_proceso'

    def action_secado(self):
        for rec in self:
            rec.state = 'secado'

    def action_control(self):
        for rec in self:
            rec.state = 'control'

    def action_terminado(self):
        for rec in self:
            rec.state = 'terminado'

    def action_entregado(self):
        for rec in self:
            rec.date_delivered = fields.Date.context_today(self)
            rec.state = 'entregado'

    def action_cancelar(self):
        for rec in self:
            rec.state = 'cancelado'

    def action_reabrir(self):
        for rec in self:
            rec.state = 'recibido'


class ColortechWorkorderLine(models.Model):
    """Línea de servicio dentro de una orden de trabajo."""
    _name = 'colortech.workorder.line'
    _description = 'Línea de Orden de Trabajo'
    _order = 'sequence, id'

    workorder_id = fields.Many2one(
        comodel_name='colortech.workorder',
        string='Orden de Trabajo',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
    )
    service_id = fields.Many2one(
        comodel_name='colortech.service',
        string='Servicio',
        required=True,
        ondelete='restrict',
    )
    description = fields.Char(
        string='Descripción',
    )
    quantity = fields.Float(
        string='Cantidad',
        default=1.0,
    )
    unit_price = fields.Float(
        string='Precio Unitario (€)',
        digits=(10, 2),
    )
    subtotal = fields.Float(
        string='Subtotal (€)',
        compute='_compute_subtotal',
        digits=(10, 2),
        store=True,
    )
    estimated_hours = fields.Float(
        string='Horas Estimadas',
    )

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.onchange('service_id')
    def _onchange_service_id(self):
        """Auto-rellenar precio y horas al seleccionar un servicio."""
        if self.service_id:
            self.unit_price = self.service_id.default_price
            self.estimated_hours = self.service_id.estimated_hours
            if not self.description:
                self.description = self.service_id.name
