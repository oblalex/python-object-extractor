import argparse
import sys

from pathlib import Path

from python_object_extractor.collections import merge_sets
from python_object_extractor.imports import group_imports_by_origin
from python_object_extractor.imports import resolve_import_conflicts
from python_object_extractor.inspection import inspect_object_with_children
from python_object_extractor.output import output
from python_object_extractor.references import make_name_from_object_reference
from python_object_extractor.references import ObjectReference
from python_object_extractor.substitutions import substitute_aliases_of_groupped_imports
from python_object_extractor.substitutions import substitute_aliases_of_imports


def load_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract Python object with its dependencies from local project."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        'object_reference',
        type=str,
        help=(
            "reference to object to extract. "
            "Example: 'importable.module:object'"
        ),
    )
    parser.add_argument(
        '-p', '--project_path',
        dest='project_path',
        type=Path,
        default='.',
        help="path to local project directory",
    )
    parser.add_argument(
        '-m', '--output_module_path',
        dest='output_module_path',
        type=Path,
        default='main.py',
        help="path to output Python module containing extracted object",
    )
    parser.add_argument(
        '-r', '--output_requirements_path',
        dest='output_requirements_path',
        type=Path,
        default='requirements.txt',
        help="path to output requirements file",
    )
    return parser.parse_args()


def main() -> None:
    args = load_args()
    project_path = str(args.project_path.absolute())

    if project_path not in sys.path:
        sys.path.insert(0, project_path)

    module_name, object_name = args.object_reference.split(':')
    object_reference = ObjectReference(
        module_name=module_name,
        object_name=object_name,
    )
    descriptors = inspect_object_with_children(
        object_reference=object_reference,
        project_path=project_path,
    )
    project_references_to_aliases = {
        x.object_reference: make_name_from_object_reference(x.object_reference)
        for x in descriptors
    }
    imports = merge_sets([x.gather_imports() for x in descriptors])
    imports = resolve_import_conflicts(imports)
    imports = substitute_aliases_of_imports(imports, project_references_to_aliases)

    all_references_to_aliases = {
        x.object_reference: x.alias or x.object_reference.object_name
        for x in imports
    }
    all_references_to_aliases[object_reference] = project_references_to_aliases[object_reference]

    substitute_aliases_of_groupped_imports(
        groupped_imports=[
            x.global_imports
            for x in descriptors
            if x.global_imports
        ],
        references_to_aliases=all_references_to_aliases,
    )

    imports = group_imports_by_origin(imports, project_path)

    output(
        module_path=args.output_module_path,
        requirements_path=args.output_requirements_path,
        descriptors=descriptors,
        imports=imports,
        references_to_aliases=all_references_to_aliases,
    )


if __name__ == '__main__':
    main()
