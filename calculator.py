import numpy as np
import json
with open('industrialist_machines.json', 'r', encoding='utf-8') as f:
    machines_data = json.load(f)



def get_crafting_info(machine_name, item_name):
    """
    Returns (time_seconds, energy_per_second, materials_dict) for the given item in the specified machine. [0] time in seconds, [1] energy per second in MF, [2] materials as a dict.
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
            time_part, energy_part = quantity.split('+')
            time_seconds = float(time_part.strip().replace('s', ''))
            # Extract energy value
            energy_str = energy_part.strip().replace('⚡', '').replace('/s', '')
            # Convert kMF, MMF, etc. to a number
            if 'MMF' in energy_str:
                energy_per_second = float(energy_str.replace('MMF', '')) * 1000000
            elif 'kMF' in energy_str:
                energy_per_second = float(energy_str.replace('kMF', '')) * 1000
            elif 'MF' in energy_str:
                energy_per_second = float(energy_str.replace('MF', ''))
            else:
                energy_per_second = float(''.join(filter(str.isdigit, energy_str)))

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


print(get_crafting_info('Advanced Assembler', 'Chair'))