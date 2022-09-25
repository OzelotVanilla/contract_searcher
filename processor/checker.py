import re
from typing import Callable
from processor.reader import PDFFile, getReadByPagesGenerator
from processor.statement_info import ItemMatchingRule, AnyRegexFulfilled, ReachPercentage, NearbyPageMatching, NearbyCharMatching

from processor.statement_info import statement_dict
from util.console import console


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


def checkDocument(pdf_path: str, skip_content_pages: bool = True) -> dict[str, bool]:
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

        skip_n_page = 2  # Contains first page
        have_found_content_page = False
        skip_content_page_finished = False
        content_checker = re.compile(r"(?:table\s+of\s+)contents?")

        has_statement_by_chairman = False

        for page_index in range(len(pdf_file)):
            # Always read next page, shuffle previous
            previous_page_text, current_page_text, next_page_text = pdf_file.getPageAndNearby(page_index)
            previous_page_text = previous_page_text.replace("\n", " ")
            current_page_text = current_page_text.replace("\n", " ")
            next_page_text = next_page_text.replace("\n", " ")

            # Always search statement by chairman first, it might before content. Check until find it.
            if not has_statement_by_chairman:
                console.sublog(f"Try to find statement by chairman at page {page_index}.", colour_rgb="124dae")
                is_found, match_info = checkAnyRegexFulFilled(
                    statement_dict["statement_by_chairman"].check_rule, "statement_by_chairman",
                    previous_page_text, current_page_text, next_page_text, page_index
                )
                if is_found:
                    result_dict["statement_by_chairman"] = has_statement_by_chairman = True
                    processMatchInfo(match_info, "statement_by_chairman")

            # Skip for "table of content" pages
            # crude: only skip first page matches "(?:table\sof\s)contents?", and its next page
            # If this function should skip potential content pages
            if skip_content_pages and (not skip_content_page_finished):
                should_skip_result, skip_content_page_finished, skip_n_page = shouldSkipThisPage(
                    skip_content_page_finished, have_found_content_page, skip_n_page, content_checker,
                    current_page_text, page_index, pdf_path
                )
                if type(should_skip_result) == bool and should_skip_result == True:
                    have_found_content_page = True
                    continue
                elif type(should_skip_result) == dict:  # Skip failed, re-do scanning finished
                    return should_skip_result

            # Check each page by all rules
            for rule_name in statement_dict.keys():
                # If already true, skip it
                if result_dict[rule_name] == True:
                    continue

                # If not already true yet
                check_rule = statement_dict[rule_name].check_rule
                is_placeholder = statement_dict[rule_name].placeholder
                if (type(check_rule) in rule_type_to_func_dict.keys()):
                    # If it is just placeholder, do not check
                    if is_placeholder:
                        continue

                    is_found, match_info = rule_type_to_func_dict[type(check_rule)](
                        check_rule, rule_name, previous_page_text, current_page_text, next_page_text, page_index
                    )
                    result_dict[rule_name] = is_found
                    if is_found:
                        processMatchInfo(match_info, rule_name)
                else:  # Unknow check_rule type
                    console.err("Check rule type \"", type(check_rule), "\" not in rule_type_to_func_dict", sep="")
                    raise NotImplementedError(type(check_rule))

    return result_dict


def processMatchInfo(match_info: MatchResultInfo, rule_name: str) -> None:
    console.sublog("Found " + rule_name, colour_rgb="b19a00")
    if match_info != None:
        match_info: MatchResultInfo = match_info
        console.sublog(
            f"- trigger text at page {match_info.trigget_at_page} (in document {match_info.trigget_at_page + 1}):",
            colour_rgb="f7b977", sep=""
        )
        console.sublog("    " + match_info.trigger_text.replace("\n", " "))
        # If has nearby
        if match_info.nearby_text != None and match_info.nearby_at_page != None:
            console.sublog(
                f"- nearby text at page {match_info.nearby_at_page} (in document {match_info.nearby_at_page + 1}):",
                colour_rgb="f7b977", sep=""
            )
            console.sublog("    " + match_info.nearby_text.replace("\n", " "))

        print()  # Give a blank line to next "Found"
    else:  # match_info unfortunately wrong.
        console.err("Unexpected none match_info")
        raise NotImplementedError("match_info: ", match_info)


def shouldSkipThisPage(skip_content_page_finished, have_found_content_page, skip_n_page,
                       content_checker, current_page_text: str,
                       page_index: int, pdf_path) -> tuple[bool, bool, int] | tuple[dict[str, bool], None, None]:
    # Check if already found first content page
    if have_found_content_page:
        # Skip required pages
        if skip_n_page > 0:
            console.sublog(f"Skipping page {page_index}:", colour_rgb="ec6d51")
            console.sublog(current_page_text.replace("\n", "  ")[0:60])
            print()
            skip_n_page -= 1
            return (True, skip_content_page_finished, skip_n_page)
        if skip_n_page == 0:  # Skip page finished
            console.sublog(
                f"No longer need to skip at page {page_index} and after:", colour_rgb="ec6d51"
            )
            console.sublog(current_page_text.replace("\n", "  ")[0:60])
            print()
            skip_content_page_finished = True
            return (True, skip_content_page_finished, skip_n_page)
    else:  # Have not found content page
        # If content not found after 5 pages, redo it now
        if page_index > 5:
            console.sublog(
                f"Maybe no table of content for file {pdf_path}. Redo without skipping...", colour_rgb="ec6d51"
            )
            return (checkDocument(pdf_path, skip_content_pages=False), None)

        # Check if this page is content page
        have_found_content_page = (content_checker.search(current_page_text) != None)
        if have_found_content_page:  # this page is content
            console.sublog(f"Found content at page {page_index}:", colour_rgb="ec6d51")
            console.sublog(current_page_text.replace("\n", "  ")[0:60])
        else:  # If not, check next page
            console.sublog(
                f"Page {page_index} seems not a content page, continue find it.", colour_rgb="ec6d51"
            )
            console.sublog(current_page_text.replace("\n", "  ")[0:60])
        print()
        return (True, skip_content_page_finished, skip_n_page)  # Whether is or not, this page should not be scanned


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
                previous_result,next_result=None,None # If no need to search before/after
                current_result = nearby_regex.search(current_page_text)

                # If need to search previous or next page
                if check_rule.search_page_before:
                    previous_result = nearby_regex.search(previous_page_text)
                if check_rule.search_page_after:
                    next_result = nearby_regex.search(next_page_text)
                
                # If found corresponding nearby
                if previous_result != None or current_result != None or next_result != None:
                    trigger_range = trigger_result.span()
                    final_result_span = None
                    final_text = None
                    if previous_result != None:
                        final_result_span = previous_result.span()
                        final_text = previous_page_text
                    elif current_result != None:
                        final_result_span = current_result.span()
                        final_text = current_page_text
                    elif next_result != None:
                        final_result_span = next_result.span()
                        final_text = next_page_text
                    match_info = MatchResultInfo(
                        trigget_at_page=page_num,
                        trigger_text=getTextAroundCrossPage(
                            current_page_text, previous_page_text, next_page_text,
                            trigger_range[0], trigger_range[1]
                        ),
                        nearby_at_page=(page_num - 1) if previous_result != None else page_num + 1,
                        nearby_text=getTextAroundInPage(
                            final_text,
                            final_result_span[0], final_result_span[1]
                        )
                    )

                    return (True, match_info)

    # All trigger failed, or no corresponding nearby
    return (False, None)


def checkNearbyCharMatching(check_rule: NearbyCharMatching, rule_name: str,
                            previous_page_text: str, current_page_text: str, next_page_text: str,
                            page_num: int) -> tuple[bool, MatchResultInfo | None]:
    for trigger_regex in check_rule.trigger_regexs:
        # Possible for having multiple match result in same page
        trigger_results = re.finditer(trigger_regex, current_page_text)

        # If found, check each result, if words around
        # If not found, this for-loop will be ignored
        for trigger_result in trigger_results:
            # Get nearby n char
            trigger_range = trigger_result.span()
            text_nearby = getTextAroundCrossPage(
                current_page_text, previous_page_text, next_page_text,
                trigger_range[0], trigger_range[1],
                around_n_char=check_rule.near_n_char, use_colour=False
            )

            # Check whether some regex can found result in it
            for nearby_regex in check_rule.search_nearby_regexs:
                nearby_result = nearby_regex.search(text_nearby.replace("ﬃ", "ffi")) # Special fix for one document
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
                        nearby_text=getTextAroundInPage(text_nearby, nearby_range[0], nearby_range[1])
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
        + ("\033[39m" if use_colour else "")               \
        + text[target_right_index:text_around_end]


def getTextAroundCrossPage(current_text: str, previous_text: str, next_text: str,
                           target_left_index: int, target_right_index: int,
                           around_n_char: int = 50, use_colour: bool = True) -> str:
    # If need to exceed left edge of current text
    left_around_text: str = None
    if target_left_index < around_n_char:
        # Include text from previous page
        left_around_text = previous_text[-1 - (around_n_char - target_left_index)
                                               :-1] + current_text[0:target_left_index]
    else:
        left_around_text = current_text[target_left_index - around_n_char:target_left_index]

    # Right side also
    right_around_text: str = None
    if len(current_text) - around_n_char < target_right_index:
        # Include text from next page
        right_around_text = current_text[target_right_index:-1] \
            + next_text[0:around_n_char - (len(current_text) - target_right_index)]
    else:
        right_around_text = current_text[target_right_index:target_right_index + around_n_char + 1]

    return ""                                                 \
        + left_around_text                                    \
        + ("\033[38;2;62;179;112m" if use_colour else "")     \
        + current_text[target_left_index:target_right_index]  \
        + ("\033[39m" if use_colour else "")                  \
        + right_around_text


def highlightText(text: str, range_left: int, range_right: int) -> str:
    return "" \
        + text[0:range_left] \
        + "\033[38;2;62;179;112m" \
        + text[range_left:range_right] \
        + "\033[39m" \
        + text[range_right:len(text)]


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
