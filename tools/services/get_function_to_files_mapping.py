import sys
from pathlib import Path
from elftools.elf.elffile import ELFFile

def get_function_file_mapping(binary_path):
    mapping = {}

    with open(binary_path, 'rb') as f:
        elf = ELFFile(f)
        if not elf.has_dwarf_info():
            return mapping

        dwarf = elf.get_dwarf_info()

        for cu in dwarf.iter_CUs():
            top_die = cu.get_top_DIE()
            comp_dir = top_die.attributes.get('DW_AT_comp_dir')
            comp_dir = comp_dir.value.decode() if comp_dir else ''
            cu_name = top_die.attributes.get('DW_AT_name')
            cu_name = cu_name.value.decode() if cu_name else None
            if not cu_name:
                continue

            cu_offset = cu.cu_offset

            line_prog = dwarf.line_program_for_CU(cu)
            file_table = line_prog.header['file_entry'] if line_prog else []
            include_dirs = line_prog.header['include_directory'] if line_prog else []

            def resolve_file(idx):
                path_of_file = ""
                if idx == 0:
                    print("cu_name -> ", cu_name)
                    path_of_file = cu_name
                entry = file_table[idx - 1]
                path_of_file = entry.name.decode() if isinstance(entry.name, bytes) else entry.name
                return Path(path_of_file).name

            # Build offset -> DIE info map (single pass)
            die_info = {}
            for die in cu.iter_DIEs():
                if die.tag != 'DW_TAG_subprogram':
                    continue
                info = {}
                name_attr = die.attributes.get('DW_AT_name')
                if name_attr:
                    info['name'] = name_attr.value.decode() if isinstance(name_attr.value, bytes) else name_attr.value
                if 'DW_AT_linkage_name' in die.attributes:
                    ln = die.attributes['DW_AT_linkage_name'].value
                    info['linkage_name'] = ln.decode() if isinstance(ln, bytes) else ln
                if 'DW_AT_specification' in die.attributes:
                    info['spec'] = die.attributes['DW_AT_specification'].value + cu_offset
                if 'DW_AT_abstract_origin' in die.attributes:
                    info['origin'] = die.attributes['DW_AT_abstract_origin'].value + cu_offset
                if 'DW_AT_low_pc' in die.attributes:
                    info['has_code'] = True
                if 'DW_AT_ranges' in die.attributes:
                    info['has_code'] = True
                if 'DW_AT_decl_file' in die.attributes:
                    info['decl_file'] = die.attributes['DW_AT_decl_file'].value
                decl = die.attributes.get('DW_AT_declaration')
                if decl and decl.value:
                    info['is_decl'] = True
                inl = die.attributes.get('DW_AT_inline')
                if inl:
                    info['is_inline'] = True

                die_info[die.offset] = info

            # Resolve name by following spec/origin chain
            def resolve_name(offset, depth=0):
                if depth > 5:
                    return None
                info = die_info.get(offset)
                if not info:
                    return None
                if 'name' in info:
                    return info['name']
                if 'spec' in info:
                    return resolve_name(info['spec'], depth + 1)
                if 'origin' in info:
                    return resolve_name(info['origin'], depth + 1)
                return None

            # Collect definitions
            for offset, info in die_info.items():
                if info.get('is_decl'):
                    continue

                # Must have code (low_pc or ranges) or be inline definition
                if not info.get('has_code') and not info.get('is_inline'):
                    continue

                func = resolve_name(offset)
                if not func:
                    continue

                if info.get('has_code'):
                    mapping[func] = Path(cu_name).name
                elif 'decl_file' in info:
                    mapping[func] = resolve_file(info['decl_file'])
    return mapping


if __name__ == "__main__":
    mapping = get_function_file_mapping(sys.argv[1])
    for func, src in sorted(mapping.items()):
        print(f"{func} -> {src}")