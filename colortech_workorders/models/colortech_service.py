
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ColortechService(models.Model):
    """Catálogo de servicios que ofrece el taller.

    Cada servicio tiene un precio base y un tiempo estimado.
    Ejemplos: Lacado completo, Personalización parcial, Restauración, etc.
    """
    _name = 'colortech.service'
    _description = 'Servicio de Personalización'
    _order = 'name'

    name = fields.Char(
        string='Nombre del Servicio',
        required=True,
    )
    code = fields.Char(
        string='Código',
        required=True,
    )
    service_type = fields.Selection(
        selection=[
            ('pintura', 'Pintura y Lacado'),
            ('personalizacion', 'Personalización'),
            ('restauracion', 'Restauración'),
            ('proteccion', 'Protección y Recubrimiento'),
            ('otro', 'Otro'),
        ],
        string='Tipo de Servicio',
        required=True,
        default='pintura',
    )
    description = fields.Text(
        string='Descripción',
    )
    default_price = fields.Float(
        string='Precio Base (€)',
        digits=(10, 2),
        default=0.0,
    )
    estimated_hours = fields.Float(
        string='Tiempo Estimado (horas)',
        default=1.0,
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)',
         'El código del servicio debe ser único.'),
    ]

    @api.constrains('default_price')
    def _check_price(self):
        for rec in self:
            if rec.default_price < 0:
                raise ValidationError(
                    'El precio no puede ser negativo.')

    @api.constrains('estimated_hours')
    def _check_hours(self):
        for rec in self:
            if rec.estimated_hours < 0:
                raise ValidationError(
                    'El tiempo estimado no puede ser negativo.')
