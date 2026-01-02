#!/usr/bin/env python3
"""Gate Quote Pro - Web Application"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

# Add app directory to path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app.models.database import get_db
from app.models.customer import Customer
from app.models.quote import Quote, QuoteItem
from app.models.materials import Material
from app.services.quote_calculator import get_calculator
from app.services.pdf_generator import get_pdf_generator
from app.services.supplier_api import get_supplier_api

# Initialize Flask app
flask_app = Flask(__name__,
    template_folder='templates',
    static_folder='static'
)
CORS(flask_app)

# Initialize database and load defaults on startup
def init_app():
    db = get_db()
    Material.load_defaults()

init_app()

# ============== Pages ==============

@flask_app.route('/')
def index():
    return render_template('index.html')

# ============== Customer API ==============

@flask_app.route('/api/customers', methods=['GET'])
def get_customers():
    search = request.args.get('search', '')
    if search:
        customers = Customer.search(search)
    else:
        customers = Customer.get_all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'email': c.email,
        'phone': c.phone,
        'address': c.address,
        'city': c.city,
        'state': c.state,
        'zip_code': c.zip_code,
        'notes': c.notes
    } for c in customers])

@flask_app.route('/api/customers', methods=['POST'])
def create_customer():
    data = request.json
    customer = Customer(
        name=data.get('name', ''),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        address=data.get('address', ''),
        city=data.get('city', ''),
        state=data.get('state', ''),
        zip_code=data.get('zip_code', ''),
        notes=data.get('notes', '')
    )
    customer.save()
    return jsonify({'id': customer.id, 'name': customer.name})

@flask_app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    customer = Customer.get_by_id(customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    data = request.json
    customer.name = data.get('name', customer.name)
    customer.email = data.get('email', customer.email)
    customer.phone = data.get('phone', customer.phone)
    customer.address = data.get('address', customer.address)
    customer.city = data.get('city', customer.city)
    customer.state = data.get('state', customer.state)
    customer.zip_code = data.get('zip_code', customer.zip_code)
    customer.notes = data.get('notes', customer.notes)
    customer.save()
    return jsonify({'success': True})

@flask_app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    customer = Customer.get_by_id(customer_id)
    if customer:
        customer.delete()
    return jsonify({'success': True})

# ============== Quote API ==============

@flask_app.route('/api/quotes', methods=['GET'])
def get_quotes():
    status = request.args.get('status')
    quotes = Quote.get_all(status=status if status else None)
    return jsonify([{
        'id': q.id,
        'quote_number': q.quote_number,
        'customer_name': q.customer.name if q.customer else 'No customer',
        'gate_type': q.gate_type,
        'width': q.width,
        'height': q.height,
        'total': q.total,
        'status': q.status,
        'created_at': str(q.created_at) if q.created_at else ''
    } for q in quotes])

@flask_app.route('/api/quotes/<int:quote_id>', methods=['GET'])
def get_quote(quote_id):
    quote = Quote.get_by_id(quote_id)
    if not quote:
        return jsonify({'error': 'Quote not found'}), 404

    return jsonify({
        'id': quote.id,
        'quote_number': quote.quote_number,
        'customer_id': quote.customer_id,
        'customer': {
            'id': quote.customer.id,
            'name': quote.customer.name,
            'email': quote.customer.email,
            'phone': quote.customer.phone,
            'address': quote.customer.address,
            'city': quote.customer.city,
            'state': quote.customer.state,
            'zip_code': quote.customer.zip_code
        } if quote.customer else None,
        'gate_type': quote.gate_type,
        'gate_style': quote.gate_style,
        'width': quote.width,
        'height': quote.height,
        'material': quote.material,
        'automation': quote.automation,
        'access_control': quote.access_control,
        'ground_type': quote.ground_type,
        'slope': quote.slope,
        'power_distance': quote.power_distance,
        'removal_needed': quote.removal_needed,
        'labor_hours': quote.labor_hours,
        'labor_rate': quote.labor_rate,
        'materials_cost': quote.materials_cost,
        'markup_percent': quote.markup_percent,
        'tax_rate': quote.tax_rate,
        'subtotal': quote.subtotal,
        'tax_amount': quote.tax_amount,
        'total': quote.total,
        'status': quote.status,
        'notes': quote.notes,
        'items': [{
            'id': item.id,
            'category': item.category,
            'description': item.description,
            'quantity': item.quantity,
            'unit': item.unit,
            'unit_cost': item.unit_cost,
            'total_cost': item.total_cost
        } for item in quote.items]
    })

@flask_app.route('/api/quotes', methods=['POST'])
def create_quote():
    data = request.json
    quote = Quote(
        customer_id=data.get('customer_id'),
        gate_type=data.get('gate_type', 'swing'),
        gate_style=data.get('gate_style', 'standard'),
        width=float(data.get('width', 12)),
        height=float(data.get('height', 6)),
        material=data.get('material', 'steel'),
        automation=data.get('automation', 'none'),
        access_control=data.get('access_control', 'none'),
        ground_type=data.get('ground_type', 'concrete'),
        slope=data.get('slope', 'flat'),
        power_distance=float(data.get('power_distance', 0)),
        removal_needed=data.get('removal_needed', False),
        notes=data.get('notes', ''),
        status=data.get('status', 'draft')
    )

    # Add items if provided
    for item_data in data.get('items', []):
        item = QuoteItem(
            category=item_data.get('category', ''),
            description=item_data.get('description', ''),
            quantity=float(item_data.get('quantity', 1)),
            unit=item_data.get('unit', 'each'),
            unit_cost=float(item_data.get('unit_cost', 0))
        )
        item.calculate_total()
        quote.items.append(item)

    quote.save()
    return jsonify({'id': quote.id, 'quote_number': quote.quote_number})

@flask_app.route('/api/quotes/<int:quote_id>', methods=['PUT'])
def update_quote(quote_id):
    quote = Quote.get_by_id(quote_id)
    if not quote:
        return jsonify({'error': 'Quote not found'}), 404

    data = request.json
    quote.customer_id = data.get('customer_id', quote.customer_id)
    quote.gate_type = data.get('gate_type', quote.gate_type)
    quote.gate_style = data.get('gate_style', quote.gate_style)
    quote.width = float(data.get('width', quote.width))
    quote.height = float(data.get('height', quote.height))
    quote.material = data.get('material', quote.material)
    quote.automation = data.get('automation', quote.automation)
    quote.access_control = data.get('access_control', quote.access_control)
    quote.ground_type = data.get('ground_type', quote.ground_type)
    quote.slope = data.get('slope', quote.slope)
    quote.power_distance = float(data.get('power_distance', quote.power_distance))
    quote.removal_needed = data.get('removal_needed', quote.removal_needed)
    quote.labor_hours = float(data.get('labor_hours', quote.labor_hours))
    quote.labor_rate = float(data.get('labor_rate', quote.labor_rate))
    quote.notes = data.get('notes', quote.notes)
    quote.status = data.get('status', quote.status)

    # Update items
    if 'items' in data:
        quote.items = []
        for item_data in data['items']:
            item = QuoteItem(
                category=item_data.get('category', ''),
                description=item_data.get('description', ''),
                quantity=float(item_data.get('quantity', 1)),
                unit=item_data.get('unit', 'each'),
                unit_cost=float(item_data.get('unit_cost', 0))
            )
            item.calculate_total()
            quote.items.append(item)

    quote.save()
    return jsonify({'success': True})

@flask_app.route('/api/quotes/<int:quote_id>', methods=['DELETE'])
def delete_quote(quote_id):
    quote = Quote.get_by_id(quote_id)
    if quote:
        quote.delete()
    return jsonify({'success': True})

@flask_app.route('/api/quotes/<int:quote_id>/status', methods=['PUT'])
def update_quote_status(quote_id):
    quote = Quote.get_by_id(quote_id)
    if not quote:
        return jsonify({'error': 'Quote not found'}), 404

    data = request.json
    quote.status = data.get('status', quote.status)
    quote.save()
    return jsonify({'success': True})

# ============== Calculate API ==============

@flask_app.route('/api/calculate', methods=['POST'])
def calculate_quote():
    data = request.json
    quote = Quote(
        gate_type=data.get('gate_type', 'swing'),
        gate_style=data.get('gate_style', 'standard'),
        width=float(data.get('width', 12)),
        height=float(data.get('height', 6)),
        material=data.get('material', 'steel'),
        automation=data.get('automation', 'none'),
        access_control=data.get('access_control', 'none'),
        ground_type=data.get('ground_type', 'concrete'),
        slope=data.get('slope', 'flat'),
        power_distance=float(data.get('power_distance', 0)),
        removal_needed=data.get('removal_needed', False)
    )

    calculator = get_calculator()
    quote = calculator.calculate_quote(quote)

    return jsonify({
        'labor_hours': quote.labor_hours,
        'labor_rate': quote.labor_rate,
        'materials_cost': quote.materials_cost,
        'markup_percent': quote.markup_percent,
        'subtotal': quote.subtotal,
        'tax_amount': quote.tax_amount,
        'total': quote.total,
        'items': [{
            'category': item.category,
            'description': item.description,
            'quantity': item.quantity,
            'unit': item.unit,
            'unit_cost': item.unit_cost,
            'total_cost': item.total_cost
        } for item in quote.items]
    })

# ============== PDF API ==============

@flask_app.route('/api/quotes/<int:quote_id>/pdf', methods=['GET'])
def generate_pdf(quote_id):
    quote = Quote.get_by_id(quote_id)
    if not quote:
        return jsonify({'error': 'Quote not found'}), 404

    generator = get_pdf_generator()
    pdf_path = generator.generate(quote)

    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Quote_{quote.quote_number}.pdf'
    )

# ============== Materials API ==============

@flask_app.route('/api/materials', methods=['GET'])
def get_materials():
    category = request.args.get('category')
    search = request.args.get('search')

    if category:
        materials = Material.get_by_category(category)
    elif search:
        materials = Material.search(search)
    else:
        materials = Material.get_all()

    return jsonify([{
        'id': m.id,
        'category': m.category,
        'name': m.name,
        'unit': m.unit,
        'cost': m.cost,
        'markup': m.markup,
        'supplier': m.supplier,
        'supplier_url': m.supplier_url
    } for m in materials])

@flask_app.route('/api/materials/categories', methods=['GET'])
def get_categories():
    return jsonify(Material.get_categories())

@flask_app.route('/api/materials', methods=['POST'])
def create_material():
    data = request.json
    material = Material(
        category=data.get('category', 'misc'),
        name=data.get('name', ''),
        unit=data.get('unit', 'each'),
        cost=float(data.get('cost', 0)),
        markup=float(data.get('markup', 1.3)),
        supplier=data.get('supplier', ''),
        supplier_url=data.get('supplier_url', '')
    )
    material.save()
    return jsonify({'id': material.id})

@flask_app.route('/api/materials/<int:material_id>', methods=['PUT'])
def update_material(material_id):
    material = Material.get_by_id(material_id)
    if not material:
        return jsonify({'error': 'Material not found'}), 404

    data = request.json
    material.category = data.get('category', material.category)
    material.name = data.get('name', material.name)
    material.unit = data.get('unit', material.unit)
    material.cost = float(data.get('cost', material.cost))
    material.markup = float(data.get('markup', material.markup))
    material.supplier = data.get('supplier', material.supplier)
    material.supplier_url = data.get('supplier_url', material.supplier_url)
    material.save()
    return jsonify({'success': True})

@flask_app.route('/api/materials/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    material = Material.get_by_id(material_id)
    if material:
        material.delete()
    return jsonify({'success': True})

# ============== Supplier Price Check API ==============

@flask_app.route('/api/price-check', methods=['POST'])
def check_price():
    data = request.json
    url = data.get('url', '')

    if not url:
        return jsonify({'error': 'URL required'}), 400

    api = get_supplier_api()
    result = api.get_price_from_url(url)

    if result:
        return jsonify({
            'supplier': result.supplier,
            'product_name': result.product_name,
            'price': result.price,
            'url': result.url,
            'in_stock': result.in_stock
        })
    else:
        return jsonify({'error': 'Could not fetch price'}), 400

@flask_app.route('/api/supplier-search', methods=['GET'])
def get_supplier_urls():
    product = request.args.get('product', '')
    api = get_supplier_api()
    urls = api.get_search_urls(product)
    return jsonify(urls)

# ============== Settings API ==============

@flask_app.route('/api/settings', methods=['GET'])
def get_settings():
    db = get_db()
    return jsonify(db.get_all_settings())

@flask_app.route('/api/settings', methods=['PUT'])
def update_settings():
    db = get_db()
    data = request.json
    for key, value in data.items():
        db.set_setting(key, str(value))
    return jsonify({'success': True})

# ============== Run Server ==============

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  Gate Quote Pro - Web Application")
    print("="*50)
    print("\n  Open in your browser:")
    print("  http://localhost:8080")
    print("\n  Press Ctrl+C to stop the server")
    print("="*50 + "\n")

    flask_app.run(host='0.0.0.0', port=8080, debug=False)
