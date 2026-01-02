"""Quote calculation service for Gate Quote Pro."""
from typing import List, Tuple
from ..models.quote import Quote, QuoteItem
from ..models.materials import Material
from ..models.database import get_db


class QuoteCalculator:
    """Service to calculate labor hours and costs for gate installations."""

    # Base labor hours by gate type
    GATE_TYPE_HOURS = {
        'swing': 4.0,
        'sliding': 6.0,
        'cantilever': 8.0,
        'bi-fold': 6.0,
        'pedestrian': 2.0
    }

    # Additional hours per foot of width (over 10ft base)
    WIDTH_FACTOR = 0.25

    # Height multiplier
    HEIGHT_MULTIPLIER = {
        'under_5': 0.8,
        '5_to_7': 1.0,
        '7_to_10': 1.3,
        'over_10': 1.6
    }

    # Material complexity factor
    MATERIAL_FACTOR = {
        'chain_link': 0.7,
        'wood': 0.9,
        'steel': 1.0,
        'aluminum': 1.0,
        'wrought_iron': 1.4
    }

    # Style complexity factor
    STYLE_FACTOR = {
        'basic': 0.8,
        'standard': 1.0,
        'ornamental': 1.5,
        'custom': 2.0
    }

    # Automation installation hours
    AUTOMATION_HOURS = {
        'none': 0.0,
        'single_swing': 3.0,
        'dual_swing': 5.0,
        'slide': 4.0
    }

    # Access control installation hours
    ACCESS_CONTROL_HOURS = {
        'none': 0.0,
        'keypad': 1.0,
        'remote': 0.5,
        'intercom': 2.0,
        'full_system': 4.0
    }

    # Ground type factor
    GROUND_FACTOR = {
        'concrete': 1.0,
        'asphalt': 1.1,
        'gravel': 1.2,
        'dirt': 1.3
    }

    # Slope factor
    SLOPE_FACTOR = {
        'flat': 1.0,
        'slight': 1.1,
        'moderate': 1.3,
        'steep': 1.6
    }

    def calculate_labor_hours(self, quote: Quote) -> float:
        """Calculate estimated labor hours for a quote."""
        # Base hours from gate type
        base_hours = self.GATE_TYPE_HOURS.get(quote.gate_type, 4.0)

        # Width adjustment (add time for gates over 10ft)
        if quote.width > 10:
            base_hours += (quote.width - 10) * self.WIDTH_FACTOR

        # Height multiplier
        if quote.height < 5:
            height_mult = self.HEIGHT_MULTIPLIER['under_5']
        elif quote.height <= 7:
            height_mult = self.HEIGHT_MULTIPLIER['5_to_7']
        elif quote.height <= 10:
            height_mult = self.HEIGHT_MULTIPLIER['7_to_10']
        else:
            height_mult = self.HEIGHT_MULTIPLIER['over_10']

        # Material factor
        material_fact = self.MATERIAL_FACTOR.get(quote.material, 1.0)

        # Style factor
        style_fact = self.STYLE_FACTOR.get(quote.gate_style, 1.0)

        # Ground condition factor
        ground_fact = self.GROUND_FACTOR.get(quote.ground_type, 1.0)

        # Slope factor
        slope_fact = self.SLOPE_FACTOR.get(quote.slope, 1.0)

        # Calculate gate installation hours
        gate_hours = base_hours * height_mult * material_fact * style_fact * ground_fact * slope_fact

        # Add automation hours
        auto_hours = self.AUTOMATION_HOURS.get(quote.automation, 0.0)

        # Add access control hours
        access_hours = self.ACCESS_CONTROL_HOURS.get(quote.access_control, 0.0)

        # Add electrical run time (0.1 hours per foot from power)
        electrical_hours = quote.power_distance * 0.1 if quote.automation != 'none' else 0.0

        # Add removal hours if needed
        removal_hours = 2.0 if quote.removal_needed else 0.0

        # Total hours
        total_hours = gate_hours + auto_hours + access_hours + electrical_hours + removal_hours

        # Round to nearest quarter hour
        return round(total_hours * 4) / 4

    def suggest_materials(self, quote: Quote) -> List[QuoteItem]:
        """Suggest materials based on quote specifications."""
        items = []

        # Get all available materials
        all_materials = {m.name.lower(): m for m in Material.get_all()}

        # Gate panel cost (based on material and size)
        gate_area = quote.width * quote.height
        material_names = {
            'steel': 'steel swing gate panel',
            'aluminum': 'aluminum swing gate panel',
            'wrought_iron': 'wrought iron gate panel',
            'wood': 'wood gate panel',
            'chain_link': 'chain link gate'
        }

        gate_name = material_names.get(quote.material, 'steel swing gate panel')
        for name, material in all_materials.items():
            if gate_name in name.lower():
                item = QuoteItem(
                    category='gates',
                    description=material.name,
                    quantity=quote.width,
                    unit=material.unit,
                    unit_cost=material.cost
                )
                item.calculate_total()
                items.append(item)
                break

        # Add posts (2 for swing gate, more for sliding)
        post_count = 2
        if quote.gate_type in ['sliding', 'cantilever']:
            post_count = 3

        for name, material in all_materials.items():
            if 'post 6x6' in name.lower():
                post_length = quote.height + 2  # Posts buried 2ft
                item = QuoteItem(
                    category='hardware',
                    description=f"{material.name} x {post_count} posts",
                    quantity=post_length * post_count,
                    unit='ft',
                    unit_cost=material.cost
                )
                item.calculate_total()
                items.append(item)
                break

        # Add hinges for swing gates
        if quote.gate_type in ['swing', 'bi-fold']:
            for name, material in all_materials.items():
                if 'heavy duty hinges' in name.lower():
                    item = QuoteItem(
                        category='hardware',
                        description=material.name,
                        quantity=2 if quote.gate_type == 'swing' else 4,
                        unit='pair',
                        unit_cost=material.cost
                    )
                    item.calculate_total()
                    items.append(item)
                    break

        # Add track system for sliding/cantilever
        if quote.gate_type == 'cantilever':
            for name, material in all_materials.items():
                if 'cantilever' in name.lower():
                    item = QuoteItem(
                        category='gates',
                        description=material.name,
                        quantity=1,
                        unit='each',
                        unit_cost=material.cost
                    )
                    item.calculate_total()
                    items.append(item)
                    break
        elif quote.gate_type == 'sliding':
            for name, material in all_materials.items():
                if 'v-track' in name.lower():
                    item = QuoteItem(
                        category='gates',
                        description=material.name,
                        quantity=1,
                        unit='each',
                        unit_cost=material.cost
                    )
                    item.calculate_total()
                    items.append(item)
                    break

        # Add latch
        for name, material in all_materials.items():
            if 'gate latch - heavy duty' in name.lower():
                item = QuoteItem(
                    category='hardware',
                    description=material.name,
                    quantity=1,
                    unit='each',
                    unit_cost=material.cost
                )
                item.calculate_total()
                items.append(item)
                break

        # Add automation if selected
        automation_items = {
            'single_swing': 'liftmaster la400',
            'dual_swing': 'mighty mule mm560',
            'slide': 'liftmaster rsl12u'
        }

        if quote.automation != 'none':
            search_term = automation_items.get(quote.automation, '')
            for name, material in all_materials.items():
                if search_term in name.lower():
                    item = QuoteItem(
                        category='operators',
                        description=material.name,
                        quantity=1 if quote.automation != 'dual_swing' else 1,
                        unit='each',
                        unit_cost=material.cost
                    )
                    item.calculate_total()
                    items.append(item)
                    break

            # Add safety photoeyes for automated gates
            for name, material in all_materials.items():
                if 'safety photoeye' in name.lower():
                    item = QuoteItem(
                        category='access_control',
                        description=material.name,
                        quantity=1,
                        unit='pair',
                        unit_cost=material.cost
                    )
                    item.calculate_total()
                    items.append(item)
                    break

        # Add access control if selected
        access_items = {
            'keypad': 'wireless keypad',
            'remote': 'remote control (pack of 3)',
            'intercom': 'intercom system - basic',
            'full_system': 'telephone entry system'
        }

        if quote.access_control != 'none':
            search_term = access_items.get(quote.access_control, '')
            for name, material in all_materials.items():
                if search_term in name.lower():
                    item = QuoteItem(
                        category='access_control',
                        description=material.name,
                        quantity=1,
                        unit='each',
                        unit_cost=material.cost
                    )
                    item.calculate_total()
                    items.append(item)
                    break

        # Add electrical if automation is used
        if quote.automation != 'none' and quote.power_distance > 0:
            for name, material in all_materials.items():
                if 'electrical wire' in name.lower():
                    item = QuoteItem(
                        category='electrical',
                        description=material.name,
                        quantity=quote.power_distance,
                        unit='ft',
                        unit_cost=material.cost
                    )
                    item.calculate_total()
                    items.append(item)
                    break

            for name, material in all_materials.items():
                if 'conduit' in name.lower():
                    item = QuoteItem(
                        category='electrical',
                        description=material.name,
                        quantity=quote.power_distance,
                        unit='ft',
                        unit_cost=material.cost
                    )
                    item.calculate_total()
                    items.append(item)
                    break

        # Add concrete for posts
        bags_per_post = 4  # About 4 bags per post hole
        post_count = 2 if quote.gate_type in ['swing', 'bi-fold', 'pedestrian'] else 3
        for name, material in all_materials.items():
            if 'concrete' in name.lower() and 'bag' in material.unit.lower():
                item = QuoteItem(
                    category='hardware',
                    description=material.name,
                    quantity=bags_per_post * post_count,
                    unit='bag',
                    unit_cost=material.cost
                )
                item.calculate_total()
                items.append(item)
                break

        # Add removal if needed
        if quote.removal_needed:
            for name, material in all_materials.items():
                if 'existing gate removal' in name.lower():
                    item = QuoteItem(
                        category='misc',
                        description=material.name,
                        quantity=1,
                        unit='each',
                        unit_cost=material.cost
                    )
                    item.calculate_total()
                    items.append(item)
                    break

        return items

    def calculate_quote(self, quote: Quote) -> Quote:
        """Calculate full quote with labor and suggested materials."""
        # Get labor rate from settings
        db = get_db()
        quote.labor_rate = float(db.get_setting('labor_rate', '125.00'))
        quote.markup_percent = float(db.get_setting('markup_percent', '30'))
        quote.tax_rate = float(db.get_setting('tax_rate', '0.0'))

        # Calculate labor hours
        quote.labor_hours = self.calculate_labor_hours(quote)

        # Suggest materials if none added
        if not quote.items:
            quote.items = self.suggest_materials(quote)

        # Calculate totals
        quote.calculate_totals()

        return quote


# Global calculator instance
_calculator = None


def get_calculator() -> QuoteCalculator:
    """Get the global calculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = QuoteCalculator()
    return _calculator
