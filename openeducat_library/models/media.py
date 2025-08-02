###############################################################################
#
#    OpenEduCat Inc
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<https://www.openeducat.org>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpMedia(models.Model):
    _name = "op.media"
    _description = "Media Details"
    _inherit = "mail.thread"
    _order = "name"
    _rec_name = "name"

    name = fields.Char('Title', size=128, required=True)
    isbn = fields.Char('ISBN Code', size=64)
    tags = fields.Many2many('op.tag', string='Tag(s)')
    author_ids = fields.Many2many(
        'op.author', string='Author(s)', required=True)
    edition = fields.Char('Edition')
    description = fields.Text('Description')
    publisher_ids = fields.Many2many(
        'op.publisher', string='Publisher(s)', required=True)
    course_ids = fields.Many2many('op.course', string='Course')
    movement_line = fields.One2many('op.media.movement', 'media_id',
                                    'Movements')
    subject_ids = fields.Many2many(
        'op.subject', string='Subjects')
    internal_code = fields.Char('Internal Code', size=64)
    queue_ids = fields.One2many('op.media.queue', 'media_id', 'Media Queue')
    unit_ids = fields.One2many('op.media.unit', 'media_id', 'Units')
    media_type_id = fields.Many2one('op.media.type', 'Media Type')
    active = fields.Boolean(default=True)
    total_units = fields.Integer('Total Units', compute='_compute_unit_statistics',
                                 help="Total number of units for this media")
    available_units = fields.Integer('Available Units', compute='_compute_unit_statistics',
                                     help="Number of available units")
    issued_units = fields.Integer('Issued Units', compute='_compute_unit_statistics',
                                  help="Number of currently issued units")
    total_movements = fields.Integer('Total Movements', compute='_compute_movement_statistics',
                                     help="Total number of movements for this media")
    current_reservations = fields.Integer('Current Reservations', compute='_compute_reservation_count',
                                          help="Number of current reservations for this media")

    _sql_constraints = [
        ('unique_name_isbn',
         'unique(isbn)',
         'ISBN code must be unique per media!'),
        ('unique_name_internal_code',
         'unique(internal_code)',
         'Internal Code must be unique per media!'),
    ]
    
    @api.depends('unit_ids', 'unit_ids.state')
    def _compute_unit_statistics(self):
        """Compute unit statistics for media.
        
        Efficiently calculates total, available, and issued units.
        """
        for record in self:
            units = record.unit_ids
            record.total_units = len(units)
            record.available_units = len(units.filtered(lambda u: u.state == 'available'))
            record.issued_units = len(units.filtered(lambda u: u.state == 'issue'))
    
    @api.depends('movement_line')
    def _compute_movement_statistics(self):
        """Compute movement statistics for media.
        
        Counts total movements for this media.
        """
        for record in self:
            record.total_movements = len(record.movement_line)
    
    @api.depends('queue_ids', 'queue_ids.state')
    def _compute_reservation_count(self):
        """Compute current reservation count.
        
        Counts active reservations for this media.
        """
        for record in self:
            record.current_reservations = len(
                record.queue_ids.filtered(lambda q: q.state in ['request', 'accept']))
    
    @api.constrains('isbn')
    def _check_isbn_format(self):
        """Validate ISBN format.
        
        Basic ISBN format validation.
        """
        for record in self:
            if record.isbn:
                # Remove hyphens and spaces for validation
                isbn_clean = record.isbn.replace('-', '').replace(' ', '')
                if not isbn_clean.isdigit():
                    raise ValidationError(_(
                        "ISBN must contain only digits and hyphens."))
                if len(isbn_clean) not in [10, 13]:
                    raise ValidationError(_(
                        "ISBN must be either 10 or 13 digits long."))
    
    def check_availability(self):
        """Check if media has available units.
        
        Returns True if at least one unit is available.
        """
        self.ensure_one()
        return self.available_units > 0
    
    def get_next_available_unit(self):
        """Get next available media unit.
        
        Returns the first available unit or False if none available.
        """
        self.ensure_one()
        return self.unit_ids.filtered(lambda u: u.state == 'available')[:1]
    
    def create_media_units(self, quantity=1):
        """Create multiple media units for this media.
        
        Args:
            quantity: Number of units to create
            
        Returns:
            Recordset of created media units
        """
        self.ensure_one()
        if quantity <= 0:
            raise ValidationError(_(
                "Quantity must be positive."))
                
        unit_vals = []
        for i in range(quantity):
            unit_vals.append({
                'name': f"{self.name} - Unit {self.total_units + i + 1}",
                'media_id': self.id,
                'state': 'available'
            })
        
        return self.env['op.media.unit'].create(unit_vals)
    
    def get_media_report(self):
        """Generate media usage report.
        
        Returns dictionary with media statistics.
        """
        self.ensure_one()
        return {
            'media_name': self.name,
            'total_units': self.total_units,
            'available_units': self.available_units,
            'issued_units': self.issued_units,
            'total_movements': self.total_movements,
            'current_reservations': self.current_reservations,
            'authors': ', '.join(self.author_ids.mapped('name')),
            'publishers': ', '.join(self.publisher_ids.mapped('name')),
            'subjects': ', '.join(self.subject_ids.mapped('name'))
        }
