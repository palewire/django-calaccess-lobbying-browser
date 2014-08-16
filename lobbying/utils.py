import re


def family_member_detector(input):
    """Looks in a string for things that look like family member references. Often, gifts are given to family members of legislators."""
    r_sibling = r'(Sister of|Brother of|Sister-in-law of|Brother-in-law of) (.+)'
    r_spouse = r'(Spouse of|Husband of|Wife of|Spouse|Partner) (.+)'
    r_child = r'(Child of|Son of|Daughter of|Daughter|Son|Son-in-law of|Daughter-in-law of )(.+)'

    response = {
        "sibling": False,
        "spouse": False,
        "child": False,
    }

    bool_sibling = re.search(r_sibling, input)
    if bool_sibling:
        response['sibling'] = {'relationship': bool_sibling.group(1), 'remainder': bool_sibling.group(2)}

    bool_spouse = re.search(r_spouse, input)
    if bool_spouse:
        response['spouse'] = {'relationship': bool_spouse.group(1), 'remainder': bool_spouse.group(2)}

    bool_child = re.search(r_child, input)
    if bool_child:
        response['child'] = {'relationship': bool_child.group(1), 'remainder': bool_child.group(2)}

    return response
