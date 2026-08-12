from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python

PY_LANGUAGE = Language(tree_sitter_python.language())
parser = Parser(PY_LANGUAGE)

CHUNKING_QUERY = """
(class_definition 
    name: (identifier) @name) @chunk
(function_definition 
    name: (identifier) @name) @chunk
"""
query = Query(PY_LANGUAGE, CHUNKING_QUERY)

def splitCodebase(codefiles):
    chunked_files = {}
    for filename, source_code in codefiles.items():
        chunks = chunk(filename, source_code)
        chunked_files[filename] = chunks
    return chunked_files

def chunk(filename, source_code):
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    
    cursor = QueryCursor(query)
    all_matches = cursor.matches(tree.root_node)
    
    chunks = []
    
    for pattern_index, match_captures in all_matches:
        if "chunk" in match_captures and "name" in match_captures:
            node = match_captures["chunk"][0]
            name_node = match_captures["name"][0]
            
            entity_name = name_node.text.decode("utf-8")
            
            chunks.append(formatChunk(node, entity_name, filename, source_bytes))
            
    return chunks

def formatChunk(node, entity_name, filename, source_bytes):
    try:
        start_line = node.start_point.row + 1
        end_line = node.end_point.row + 1
    except AttributeError:
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
    code_snippet = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
    
    return {
        "text": code_snippet,
        "metadata": {
            "filename": filename,
            "entity_name": entity_name,
            "entity_type": "class" if node.type == "class_definition" else "function",
            "start_line": start_line,
            "end_line": end_line
        }
    }
