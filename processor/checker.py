from typing import Callable
from processor.reader import PDFFile, getReadByPagesGenerator
from processor.statement_info import ItemMatchingRule, AnyRegexFulfilled, ReachPercentage, NearbyPageMatching, NearbyCharMatching

from processor.statement_info import statement_dict
from util.console import console


class MatchResultInfo:
    ...


def checkDocument(pdf_path: str) -> dict[str, bool]:
    """
    Check the whole document whether it fulfill requirement or not
    return {requirement_name: is_fulfilled} Example: {"statement_by_chairman": true}
    """
    result_dict = dict.fromkeys(statement_dict.keys())

    # If find near, search may cross the page.
    # Read pages by pages until end
    with PDFFile(pdf_path) as pdf_file:
        # Clear previous reach_percentage dict
        global file_check_reach_percentage_result
        file_check_reach_percentage_result.clear()

        for page_index in range(len(pdf_file)):
            # Always read next page, shuffle previous
            previous_page_text, current_page_text, next_page_text = pdf_file.getPageAndNearby(page_index)

            # Check each page by all rules
            for rule_name in statement_dict.keys():
                # If already true, skip it
                if result_dict[rule_name] == True:
                    continue

                # If not already true yet
                check_rule = statement_dict[rule_name].check_rule
                if type(check_rule) in rule_type_to_func_dict.keys():
                    is_found, match_info = rule_type_to_func_dict[type(check_rule)](
                        check_rule, rule_name, previous_page_text, current_page_text, next_page_text, page_index
                    )
                    result_dict[rule_name] = is_found
                    if is_found:
                        console.sublog("Found " + rule_name, colour_rgb="b19a00")
                        if match_info != None:
                            match_info: MatchResultInfo = match_info
                            console.sublog(
                                "- trigger text at page ", match_info.trigget_at_page, ":",
                                colour_rgb="f7b977", sep=""
                            )
                            console.sublog("    " + match_info.trigger_text.replace("\n", " "))
                            # If has nearby
                            if match_info.nearby_text != None and match_info.nearby_at_page != None:
                                console.sublog(
                                    "- nearby text at page ", match_info.nearby_at_page, ":",
                                    colour_rgb="f7b977", sep=""
                                )
                                console.sublog("    " + match_info.nearby_text.replace("\n", " ") + "\n")
                        else:  # match_info unfortunately wrong.
                            console.err("Unexpected none match_info")
                            raise NotImplementedError("match_info: ", match_info)
                else:  # Unknow check_rule type
                    console.err("Check rule type \"", type(check_rule), "\" not in rule_type_to_func_dict", sep="")
                    raise NotImplementedError(type(check_rule))

    return result_dict


def checkAnyRegexFulFilled(check_rule: AnyRegexFulfilled,
                           rule_name: str, toss_1, current_page_text: str, toss_2,
                           page_num: int) -> tuple[bool, MatchResultInfo | None]:
    """
    If any regex is matched, considered true
    """
    for regex in check_rule.regexs:
        result = regex.search(current_page_text)
        if result != None:
            # Return with match info to help check where it matches
            match_info: MatchResultInfo = MatchResultInfo(
                trigger_text=getTextAroundInPage(current_page_text, result.span()[0], result.span()[1]),
                trigget_at_page=page_num
            )
            return (True, match_info)

    return (False, None)


def checkReachPercentage(check_rule: ReachPercentage, rule_name: str,
                         toss_1, current_page_text: str, toss_2,
                         page_num: int) -> tuple[bool, MatchResultInfo | None]:
    global file_check_reach_percentage_result

    # Initialize if not
    file_check_reach_percentage_result.setdefault(rule_name, [])

    # If found, put the index of regex into the list
    for (i, regex) in enumerate(check_rule.regexs):
        # If already checked
        if i in file_check_reach_percentage_result[rule_name]:
            continue

        # If found, append index
        if len(regex.findall(current_page_text)) > 0:
            file_check_reach_percentage_result[rule_name].append(i)

    # Return if that reached the percentage: passed / total
    passed_rate = len(file_check_reach_percentage_result[rule_name]) / len(check_rule.regexs)
    if passed_rate >= check_rule.percentage / 100:
        return True, MatchResultInfo(trigger_text="Not Implemented", trigget_at_page=-1)
    else:
        return (False, None)


def checkNearbyPagesMatching(check_rule: NearbyPageMatching, rule_name: str,
                             previous_page_text: str, current_page_text: str, next_page_text: str,
                             page_num: int) -> tuple[bool, MatchResultInfo | None]:
    for trigger_regex in check_rule.trigger_regexs:
        # If found, check if words around
        trigger_result = trigger_regex.search(current_page_text)
        if trigger_result != None:
            # Search nearby pages
            for nearby_regex in check_rule.search_nearby_regexs:
                # Search nearby in two nearby pages
                previous_result = nearby_regex.search(previous_page_text)
                next_result = nearby_regex.search(next_page_text)
                # If found corresponding nearby
                if previous_result != None or next_result != None:
                    trigger_range = trigger_result.span()
                    match_info = MatchResultInfo(
                        trigget_at_page=page_num,
                        trigger_text=getTextAroundCrossPage(
                            current_page_text, previous_page_text, next_page_text,
                            trigger_range[0], trigger_range[1]
                        ),
                        nearby_at_page=(page_num - 1) if previous_result != None else page_num + 1,
                        nearby_text=getTextAroundInPage(
                            previous_page_text if previous_result != None else next_page_text,
                            (previous_result.span() if previous_result != None else next_result.span())[0],
                            (previous_result.span() if previous_result != None else next_result.span())[1]
                        )
                    )

                    return (True, match_info)

    # All trigger failed, or no corresponding nearby
    return (False, None)


def checkNearbyCharMatching(check_rule: NearbyCharMatching, rule_name: str,
                            previous_page_text: str, current_page_text: str, next_page_text: str,
                            page_num: int) -> tuple[bool, MatchResultInfo | None]:
    for trigger_regex in check_rule.trigger_regexs:
        # If found, check if words around
        trigger_result = trigger_regex.search(current_page_text)
        if trigger_result != None:
            # Get nearby n char
            trigger_range = trigger_result.span()
            text_nearby = getTextAroundCrossPage(
                current_page_text, previous_page_text, next_page_text,
                trigger_range[0], trigger_range[1],
                around_n_char=check_rule.near_n_char, use_colour=False
            )

            # Check whether some regex can found result in it
            for nearby_regex in check_rule.search_nearby_regexs:
                nearby_result = nearby_regex.search(text_nearby)
                # If found result
                if nearby_result != None:
                    nearby_range = nearby_result.span()
                    match_info = MatchResultInfo(
                        trigget_at_page=page_num,
                        trigger_text=getTextAroundCrossPage(
                            current_page_text, previous_page_text, next_page_text,
                            trigger_range[0], trigger_range[1]
                        ),
                        nearby_at_page=page_num,
                        nearby_text=getTextAroundCrossPage(
                            current_page_text, previous_page_text, next_page_text,
                            nearby_range[0], nearby_range[1]
                        )
                    )

                    return (True, match_info)

    # All trigger failed, or no corresponding nearby
    return (False, None)


def getTextAroundInPage(text: str, target_left_index: int, target_right_index: int,
                        around_n_char: int = 50, use_colour: bool = True) -> str:
    text_around_start = (target_left_index - around_n_char) if target_left_index >= around_n_char else 0
    str_max_len = len(text)
    text_around_end = (target_right_index + around_n_char) \
        if (target_right_index + around_n_char < str_max_len) else str_max_len - 1

    return ""                                              \
        + text[text_around_start:target_left_index]        \
        + ("\033[38;2;62;179;112m" if use_colour else "")  \
        + text[target_left_index:target_right_index]       \
        + ("\033[39m" if use_colour else "")           \
        + text[target_right_index:text_around_end]


def getTextAroundCrossPage(current_text: str, previous_text: str, next_text: str,
                           target_left_index: int, target_right_index: int,
                           around_n_char: int = 50, use_colour: bool = True) -> str:
    # If need to exceed left edge of current text
    left_around_text: str = None
    if target_left_index < around_n_char:
        # Include text from previous page
        left_around_text = previous_text[-1 - (around_n_char - target_left_index):-1] + current_text[0:target_left_index]
    else:
        left_around_text = current_text[target_left_index - around_n_char:target_left_index]

    # Right side also
    right_around_text: str = None
    if len(current_text) - 60 < target_right_index:
        # Include text from next page
        right_around_text = current_text[target_right_index:-1] \
            + next_text[0:60 - (len(current_text) - target_right_index)]
    else:
        right_around_text = current_text[target_right_index:target_right_index + 60 + 1]

    return ""                                                 \
        + left_around_text                                    \
        + ("\033[38;2;62;179;112m" if use_colour else "")     \
        + current_text[target_left_index:target_right_index]  \
        + ("\033[39m" if use_colour else "")                  \
        + right_around_text


# {"rule_name": num_of_fulfilled}, example: {"rule_a": 3}, rule_a has 4 members, 3 fulfilled.
file_check_reach_percentage_result: dict[str, list[int]] = dict()


rule_type_to_func_dict: dict[type, Callable[[ItemMatchingRule, str, str, str, str, int], tuple[bool, MatchResultInfo]]] = {
    AnyRegexFulfilled: checkAnyRegexFulFilled,
    ReachPercentage: checkReachPercentage,
    NearbyPageMatching: checkNearbyPagesMatching,
    NearbyCharMatching: checkNearbyCharMatching
}


class MatchResultInfo:
    trigget_at_page: int
    trigger_text: str
    nearby_at_page: int | None
    nearby_text: str | None

    def __init__(self, trigget_at_page: int, trigger_text: str, nearby_at_page: int = None, nearby_text: str = None) -> None:
        self.trigget_at_page = trigget_at_page
        self.trigger_text = trigger_text
        self.nearby_at_page = nearby_at_page
        self.nearby_text = nearby_text
