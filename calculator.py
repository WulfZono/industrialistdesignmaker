import numpy as np
import sympy
import json
import re
import matplotlib.pyplot as plt
with open('industrialist_machines.json', 'r', encoding='utf-8') as f:
    machines_data = json.load(f)

def parse_quantity(quantity):
    """
    Parses a quantity
    Returns (time_seconds, energy_per_second)
    """
    # Remove spaces
    parts = [p.strip() for p in quantity.split('+')]
    time_seconds = None
    energy_per_second = None

    for part in parts:
        # Look for time
        time_match = re.search(r'([\d.]+)\s*s', part)
        if time_match:
            time_seconds = float(time_match.group(1))
        # Look for energy
        energy_match = re.search(r'([\d.]+)\s*(MMF|kMF|MF)', part)
        if energy_match:
            value = float(energy_match.group(1))
            unit = energy_match.group(2)
            if unit == 'MMF':
                value *= 1_000_000
            elif unit == 'kMF':
                value *= 1_000
            # MF is base unit
            energy_per_second = value

    return time_seconds, energy_per_second

def get_crafting_info(machine_name, item_name):
    """
    Returns (time_seconds, energy_per_second) for the given item in the specified machine. [0] time in seconds, [1] energy per second in MF
    """
    # Find the machine
    machine = next((m for m in machines_data if m['name'].lower() == machine_name.lower()), None)
    if not machine or not machine.get('recipe'):
        return None

    # Find the recipe for the item
    for recipe in machine['recipe']:
        if item_name.lower() in recipe['output'].lower():
            # Parse time and energy
            quantity = recipe['quantity']
            time_seconds, energy_per_second = parse_quantity(quantity)

            # Parse materials
            materials = {}
            for mat in recipe['material'].replace('\n', '+').split('+'):
                mat = mat.strip()
                if 'x' in mat:
                    qty, name = mat.split('x', 1)
                    try:
                        qty = float(qty)
                    except ValueError:
                        qty = qty
                    materials[name.strip()] = qty
            return time_seconds, energy_per_second, materials
    return None

def find_all_crafting_methods(item_name):
    """
    Returns a list of (machine_name, time_seconds, energy_per_second, materials_dict, output_count)
    for every machine that can craft the given item.
    """
    results = []
    for machine in machines_data:
        if not machine.get('recipe'):
            continue
        for recipe in machine['recipe']:
            output_field = recipe.get('output', '')
            # Check if this recipe produces the item
            if item_name.lower() in output_field.lower():
                quantity = recipe['quantity']
                time_seconds, energy_per_second = parse_quantity(quantity)
                # Parse materials
                materials = {}
                material_str = recipe.get('material', '')
                if material_str:
                    for mat in material_str.replace('\n', '+').split('+'):
                        mat = mat.strip()
                        if 'x' in mat:
                            qty, name = mat.split('x', 1)
                            try:
                                qty = float(qty)
                            except ValueError:
                                qty = qty
                            materials[name.strip()] = qty
                # Parse output count
                output_count = 1
                match = re.match(r'(\d+)\s*x\s*(.+)', output_field)
                if match:
                    output_count = int(match.group(1))
                results.append((machine.get('name', 'Unknown'), time_seconds, energy_per_second, materials, output_count))
    return results
print(find_all_crafting_methods("Steel Ingot"))
for item in find_all_crafting_methods("Steel Ingot"):
    print(f"Machine: {item[0]}, Time: {item[1]}s, Energy: {item[2]} MF/s, Materials: {item[3]}, Output Count: {item[4]}")
def build_recipe_matrix(item_name):
    """
    Builds a matrix for all recipes that produce item_name.
    Adds an extractor column for raw materials.
    Rows: unique materials/items.
    Columns: each recipe for item_name, plus extractor columns for raw materials.
    Consumed materials are negative, produced item is positive.
    """
    recipes = find_all_crafting_methods(item_name)
    # Collect all unique materials/items
    all_materials = set()
    for _, _, _, materials, _ in recipes:
        all_materials.update(materials.keys())
    all_materials.add(item_name)
    all_materials = sorted(all_materials)
    material_idx = {mat: i for i, mat in enumerate(all_materials)}

    # Identify raw materials (those that never appear as outputs in any recipe)
    all_outputs = set()
    for machine in machines_data:
        if not machine.get('recipe'):
            continue
        for recipe in machine['recipe']:
            output_field = recipe.get('output', '')
            match = re.match(r'(\d+)\s*x\s*(.+)', output_field)
            if match:
                output_name = match.group(2).strip()
            else:
                output_name = output_field.strip()
            all_outputs.add(output_name)
    raw_materials = [mat for mat in all_materials if mat not in all_outputs or mat == item_name]

    # Build matrix: original recipes + extractor columns for raw materials
    num_recipes = len(recipes)
    num_extractors = len(raw_materials)
    matrix = np.zeros((len(all_materials), num_recipes + num_extractors))

    # Fill in recipe columns
    for col, (machine, time, energy, materials, output_count) in enumerate(recipes):
        for mat, qty in materials.items():
            row = material_idx[mat]
            matrix[row, col] = -qty
        row = material_idx[item_name]
        matrix[row, col] = output_count

    # Fill in extractor columns
    for i, raw in enumerate(raw_materials):
        col = num_recipes + i
        row = material_idx[raw]
        matrix[row, col] = 1  # Extractor "recipe": produces 1 unit of raw material

    # Print matrix
    print("Materials/Items:", all_materials)
    print("Each column is a recipe for:", item_name, "+ extractor columns for raw materials")
    print(matrix)
    return all_materials, matrix

def calculate_rref(matrix):
    """
    Calculates the reduced row echelon form of the given matrix.
    Returns the RREF matrix and pivot columns.
    """
    sympy_matrix = sympy.Matrix(matrix)
    rref_matrix, pivots = sympy_matrix.rref()
    return np.array(rref_matrix).astype(np.float64), pivots

def build_augmented_matrix(item_name, input_vector):
    """
    Builds an augmented matrix by appending the input_vector as the last column
    to the recipe matrix for item_name.
    """
    all_materials, matrix = build_recipe_matrix(item_name)
    input_vector = np.array(input_vector).reshape(-1, 1)
    if input_vector.shape[0] != matrix.shape[0]:
        raise ValueError("Input vector length must match number of materials/items (rows) in the matrix.")
    augmented = np.hstack((matrix, input_vector))
    print("Augmented matrix:")
    print(augmented)
    return augmented



# Example usage after your RREF calculation:
# Only works if your system has 2 variables (2 columns before the augmented column)
all_materials, matrix = build_recipe_matrix("Steel Ingot")
input_vector = [0] * (len(all_materials) - 1) + [10]
augmented = build_augmented_matrix("Steel Ingot", input_vector)
rref, pivots = calculate_rref(augmented)

