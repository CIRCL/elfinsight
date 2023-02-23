import pdb

from elftools.elf.hash import GNUHashTable
from elftools.elf.sections import Section
from elftools.elf.elffile import ELFFile

class dELFFile(ELFFile):

    def _make_gnu_hash_section(self, section_header, name):
        linked_symtab_index = section_header['sh_link']
        symtab_section = self.get_section(linked_symtab_index)
        return DetailedGNUHashSection(
            section_header, name, self, symtab_section)


class DetailedGNUHashTable(GNUHashTable):
    def matches_bloom(self, H1):
        """ Helper function to check if the given hash could be in the hash
            table by testing it against the bloom filter.
             _matched_bloom no longer private
        """
        arch_bits = self.elffile.elfclass
        H2 = H1 >> self.params['bloom_shift']
        word_idx = int(H1 / arch_bits) % self.params['bloom_size']
        BITMASK = (1 << (H1 % arch_bits)) | (1 << (H2 % arch_bits))
        return (self.params['bloom'][word_idx] & BITMASK) == BITMASK

    def export_bloom(self):
        # don't mind the string repr too much, the underlying value is correct.
        return self.params['bloom'][0].to_bytes((self.params['bloom'][0].bit_length() + 7) // 8, byteorder='big')

    def export_binary_bloom(self):
        for i in self.params['bloom']:
            return f"{i:0b}"

    def slow_match_str(self, symbol):
        H1 = self.gnu_hash(symbol)
        arch_bits = self.elffile.elfclass
        print(f"[+] Matching {H1:64b}")
        print(f"[+] arch     {arch_bits}")
        print(f"[+] shift    {self.params['bloom_shift']}")
        print(f"[+] bloomsize{self.params['bloom_size']}")
        H2 = H1 >> self.params['bloom_shift']
        print(f"[+] H2       {H2:64b}")
        word_idx = int(H1 / arch_bits) % self.params['bloom_size']
        print(f"[+] word_idx {word_idx:64b}")
        print(f"[+] half BT1 {(1 << (H1 % arch_bits)):64b}")
        print(f"[+] half BT2 {(1 << (H2 % arch_bits)):64b}")
        BITMASK = (1 << (H1 % arch_bits)) | (1 << (H2 % arch_bits))
        print(f"[+] BITMASK  {BITMASK:64b}")
        print(f"[+] bloom    {self.params['bloom'][word_idx]:64b}")
        print("[+] & ")
        print(f"[+] result {(self.params['bloom'][word_idx] & BITMASK) == BITMASK}")

class DetailedGNUHashSection(Section, DetailedGNUHashTable):
    """ Section representation of a GNU hash table. In regular ELF files, this
        allows us to use the common functions defined on Section objects when
        dealing with the hash table.
    """
    def __init__(self, header, name, elffile, symboltable):
        Section.__init__(self, header, name, elffile)
        DetailedGNUHashTable.__init__(self, elffile, self['sh_offset'], symboltable)