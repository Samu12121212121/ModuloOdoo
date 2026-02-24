
from odoo import models, fields


class ColortechDeviceType(models.Model):
    """Tipos de dispositivos que se pueden personalizar.

    Ejemplos: Móvil, Consola, Portátil, Auriculares, Tablet, etc.
    """
    _name = 'colortech.device.type'
    _description = 'Tipo de Dispositivo'
    _order = 'name'

    name = fields.Char(
        string='Tipo de Dispositivo',
        required=True,
    )
    code = fields.Char(
        string='Código',
        required=True,
    )
    description = fields.Text(
        string='Descripción',
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)',
         'El código del tipo de dispositivo debe ser único.'),
    ]
