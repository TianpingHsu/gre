# coding: utf-8

import re
from collections import defaultdict

class GREParser:
    def __init__(self, filename):
        with open(filename, encoding='utf-8') as f:
            self.text = f.read()
        self.groups = []
        self.anchor_dict = {}
        self.root_dict = defaultdict(list)
        self.parse()

    def parse(self):
        # Split groups by two or more newlines
        group_texts = re.split(r'\n\s*\n', self.text.strip())
        for group in group_texts:
            lines = [l for l in group.strip().split('\n') if l.strip()]
            if not lines:
                continue
            anchor_line = lines[0]
            anchor, synonyms, antonyms, meanings = self.parse_anchor_line(anchor_line)
            derived_blocks, contexts = self.parse_blocks_and_contexts(lines[1:])
            group_data = {
                'anchor': anchor,
                'synonyms': synonyms,
                'antonyms': antonyms,
                'meanings': meanings,
                'roots': [],
                'derived': [],
                'contexts': contexts
            }
            for block in derived_blocks:
                root, root_meaning, derived_words = block
                group_data['roots'].append({'root': root, 'meaning': root_meaning})
                group_data['derived'].extend(derived_words)
                self.root_dict[root].append(anchor)
                for dw in derived_words:
                    if 'root' in dw:
                        self.root_dict[dw['root']].append(dw['word'])
            self.groups.append(group_data)
            self.anchor_dict[anchor] = group_data

    def parse_anchor_line(self, line):
        # e.g. "obdurate hard-boiled obstinate"
        # or "obscure cover; unclear opaque esoteric; unknown"
        tokens = re.findall(r'(<[^>]+>|![^\s;]+|[^\s;]+|;)', line)
        anchor = None
        synonyms = []
        antonyms = []
        meanings = []
        cur_meaning = []
        for t in tokens:
            if t == ';':
                if cur_meaning:
                    meanings.append(' '.join(cur_meaning).strip())
                    cur_meaning = []
                continue
            if anchor is None:
                anchor = t.strip('<>!')
                cur_meaning.append(anchor)
            elif t.startswith('!'):
                antonyms.append(t[1:])
            elif t.startswith('<') and t.endswith('>'):
                synonyms.append(t[1:-1])
                cur_meaning.append(t[1:-1])
            else:
                synonyms.append(t)
                cur_meaning.append(t)
        if cur_meaning:
            meanings.append(' '.join(cur_meaning).strip())
        return anchor, synonyms, antonyms, meanings

    def parse_blocks_and_contexts(self, lines):
        derived_blocks = []
        contexts = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i].strip()
            if line.startswith('{'):
                # parse derived block
                block_lines = []
                i += 1
                while i < n and not lines[i].strip().startswith('}'):
                    block_lines.append(lines[i].strip())
                    i += 1
                # skip the closing '}'
                i += 1
                if block_lines:
                    root, root_meaning, derived_words = self.parse_derived_block(block_lines)
                    derived_blocks.append((root, root_meaning, derived_words))
            elif line.startswith('['):
                # parse context
                context_lines = []
                i += 1
                while i < n and not lines[i].strip().startswith(']'):
                    context_lines.append(lines[i].strip().strip('"'))
                    i += 1
                i += 1  # skip closing ']'
                contexts.extend(context_lines)
            else:
                i += 1
        return derived_blocks, contexts

    def parse_derived_block(self, lines):
        # first line: (root): meaning
        if not lines:
            return None, None, []
        m = re.match(r'\(([^)]+)\):\s*(.*)', lines[0])
        if m:
            root = m.group(1)
            root_meaning = m.group(2)
            derived_words = []
            for w in lines[1:]:
                if w:
                    derived_words.append({'word': w, 'root': root})
            return root, root_meaning, derived_words
        else:
            # e.g. just a word, not a root
            root = lines[0]
            root_meaning = ''
            derived_words = []
            for w in lines[1:]:
                if w:
                    derived_words.append({'word': w, 'root': root})
            return root, root_meaning, derived_words

    def query_anchor(self, anchor):
        data = self.anchor_dict.get(anchor)
        if not data:
            print(f'No entry for {anchor}')
            return
        print(f"Anchor: {data['anchor']}")
        print(f"Meanings: {'; '.join(data['meanings'])}")
        if data['synonyms']:
            print(f"Synonyms: {', '.join(data['synonyms'])}")
        if data['antonyms']:
            print(f"Antonyms: {', '.join(data['antonyms'])}")
        if data['roots']:
            print("Roots:")
            for r in data['roots']:
                print(f"  {r['root']}: {r['meaning']}")
        if data['derived']:
            print("Derived words:")
            for d in data['derived']:
                print(f"  {d['word']} (root: {d['root']})")
        if data['contexts']:
            print("Contexts:")
            for c in data['contexts']:
                print(f"  {c}")

    def query_root(self, root):
        words = set(self.root_dict.get(root, []))
        if not words:
            print(f'No words found for root {root}')
            return
        print(f"Words for root '{root}':")
        for w in words:
            print(f"  {w}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python gre_parser.py <filename>")
        exit(1)
    parser = GREParser(sys.argv[1])
    while True:
        cmd = input("Enter 'a <word>' to query anchor, 'r <root>' to query root, or 'q' to quit: ").strip()
        if cmd == 'q':
            break
        elif cmd.startswith('a '):
            anchor = cmd[2:].strip()
            parser.query_anchor(anchor)
        elif cmd.startswith('r '):
            root = cmd[2:].strip()
            parser.query_root(root)
        else:
            print("Unknown command.")
