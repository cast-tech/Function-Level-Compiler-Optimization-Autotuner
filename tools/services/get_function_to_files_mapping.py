import sys
import os
from elftools.elf.elffile import ELFFile

def get_function_file_mapping(binary_path):
    with open(binary_path, 'rb') as f:
        elffile = ELFFile(f)
        if not elffile.has_dwarf_info():
            return {}

        dwarf_info = elffile.get_dwarf_info()
        results = {}

        for CU in dwarf_info.iter_CUs():
            line_program = dwarf_info.line_program_for_CU(CU)
            file_names = line_program.header.file_entry
            
            for DIE in CU.iter_DIEs():
                if DIE.tag == 'DW_TAG_subprogram':
                    name_attr = DIE.attributes.get('DW_AT_name')
                    file_idx_attr = DIE.attributes.get('DW_AT_decl_file')
                    
                    if name_attr and file_idx_attr:
                        func_name = name_attr.value.decode('utf-8', errors='ignore')
                        file_idx = file_idx_attr.value - 1
                        
                        if 0 <= file_idx < len(file_names):
                            file_name = file_names[file_idx].name.decode('utf-8')
                            results[func_name] = file_name

        return results

if __name__ == "__main__":
    mapping = get_function_file_mapping(sys.argv[1])
    for func, src in sorted(mapping.items()):
        print(f"{func} -> {src}")