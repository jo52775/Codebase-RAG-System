import tree_sitter_python
from tree_sitter import Language, Parser, Query, QueryCursor

PY_LANGUAGE = Language(tree_sitter_python.language())
parser = Parser(PY_LANGUAGE)

CHUNKING_QUERY = """
(class_definition 
    name: (identifier) @name) @chunk
(function_definition 
    name: (identifier) @name) @chunk
"""
query = Query(PY_LANGUAGE, CHUNKING_QUERY)


def splitCodebase(codefiles, repository_name = "tinyDB"):
    all_functions = []
    all_classes = []

    for filename, source_code in codefiles.items():
        functions, classes = chunk_file(filename, source_code, repository_name)
        all_functions.extend(functions)
        all_classes.extend(classes)

    return all_functions, all_classes


def chunk_file(filename, source_code, repository_name):
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)

    cursor = QueryCursor(query)
    all_matches = cursor.matches(tree.root_node)

    function_chunks = []
    class_chunks = []

    for pattern_index, match_captures in all_matches:
        if "chunk" in match_captures and "name" in match_captures:
            node = match_captures["chunk"][0]
            name_node = match_captures["name"][0]
            entity_name = name_node.text.decode("utf-8")

            if node.type == "function_definition":
                func_chunk = format_function_chunk(
                    node, entity_name, filename, source_bytes, repository_name
                )
                function_chunks.append(func_chunk)

            elif node.type == "class_definition":
                cls_chunk = format_class_chunk(
                    node, entity_name, filename, source_bytes, repository_name
                )
                class_chunks.append(cls_chunk)

    return function_chunks, class_chunks


def build_fqn(filename, node):
    ancestors = []
    curr = node
    while curr is not None:
        if curr.type in ("class_definition", "function_definition"):
            name_node = curr.child_by_field_name("name")
            if name_node:
                ancestors.append(name_node.text.decode("utf-8"))
        curr = curr.parent

    ancestors.reverse()
    scoped_path = ".".join(ancestors)
    return f"{filename}::{scoped_path}" if scoped_path else filename


def get_parents(node, filename):
    parent_fqn = None
    parent_class_fqn = None

    curr = node.parent
    while curr is not None:
        if curr.type in ("class_definition", "function_definition"):
            if parent_fqn is None:
                parent_fqn = build_fqn(filename, curr)

            if curr.type == "class_definition" and parent_class_fqn is None:
                parent_class_fqn = build_fqn(filename, curr)

        curr = curr.parent

    return parent_fqn, parent_class_fqn


def extract_class_skeleton(class_node, source_bytes):
    """Extracts docstring, class header, __init__ body, and sibling method signatures."""
    body_node = class_node.child_by_field_name("body")
    if not body_node:
        return source_bytes[class_node.start_byte : class_node.end_byte].decode(
            "utf-8"
        )

    skeleton_parts = []

    # Get class declaration header (everything up to body ':')
    header_bytes = source_bytes[class_node.start_byte : body_node.start_byte]
    skeleton_parts.append(header_bytes.decode("utf-8").strip())

    for child in body_node.children:
        # Include docstrings / pass / assignments at top level of class
        if child.type in ("expression_statement", "assignment"):
            expr_text = source_bytes[child.start_byte : child.end_byte].decode(
                "utf-8"
            )
            skeleton_parts.append(f"    {expr_text}")

        elif child.type == "function_definition":
            func_name_node = child.child_by_field_name("name")
            func_name = (
                func_name_node.text.decode("utf-8") if func_name_node else ""
            )

            if func_name in ("__init__", "__post_init__"):
                # Preserve constructor full body
                init_text = source_bytes[
                    child.start_byte : child.end_byte
                ].decode("utf-8")
                indented_init = "\n".join(
                    f"    {line}" for line in init_text.splitlines()
                )
                skeleton_parts.append(indented_init)
            else:
                # Truncate method body to signature only
                params_node = child.child_by_field_name("parameters")
                return_type_node = child.child_by_field_name("return_type")

                params = (
                    source_bytes[
                        params_node.start_byte : params_node.end_byte
                    ].decode("utf-8")
                    if params_node
                    else "()"
                )
                ret = (
                    f" -> {source_bytes[return_type_node.start_byte:return_type_node.end_byte].decode('utf-8')}"
                    if return_type_node
                    else ""
                )

                # Capture method docstring if available
                docstring = ""
                func_body = child.child_by_field_name("body")
                if func_body and func_body.children:
                    first_stmt = func_body.children[0]
                    if (
                        first_stmt.type == "expression_statement"
                        and first_stmt.children[0].type == "string"
                    ):
                        docstring = f"\n        {source_bytes[first_stmt.start_byte:first_stmt.end_byte].decode('utf-8')}"

                skeleton_parts.append(
                    f"    def {func_name}{params}{ret}:{docstring}\n        ..."
                )

    return "\n".join(skeleton_parts)


def get_line_numbers(node):
    return node.start_point[0] + 1, node.end_point[0] + 1


def format_function_chunk(
    node, entity_name, filename, source_bytes, repository_name
):
    start_line, end_line = get_line_numbers(node)
    entity_fqn = build_fqn(filename, node)
    parent_fqn, parent_class_fqn = get_parents(node, filename)

    return {
        "raw_code_text": source_bytes[
            node.start_byte : node.end_byte
        ].decode("utf-8"),
        "filename": filename,
        "entity_fqn": entity_fqn,
        "parent_fqn": parent_fqn,
        "parent_class_fqn": parent_class_fqn,
        "start_line": start_line,
        "end_line": end_line,
        "code_repository": repository_name,
    }


def format_class_chunk(
    node, entity_name, filename, source_bytes, repository_name
):
    start_line, end_line = get_line_numbers(node)
    fqn = build_fqn(filename, node)
    skeleton_text = extract_class_skeleton(node, source_bytes)

    return {
        "fqn": fqn,
        "raw_code_text": source_bytes[
            node.start_byte : node.end_byte
        ].decode("utf-8"),
        "filename": filename,
        "skeleton_text": skeleton_text,
        "start_line": start_line,
        "end_line": end_line,
        "code_repository": repository_name,
    }