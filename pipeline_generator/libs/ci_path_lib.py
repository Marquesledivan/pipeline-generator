from pathlib import Path
from typing import List

import hcl
import pkg_resources

from pipeline_generator.config.constants import (
    IGNORE_RE_LIST,
    TERRAGRUNT_RE_LIST,
)
from pipeline_generator.models.ci_path import CiPath


def get_path_list(base_path, file_pattern) -> List[Path]:
    p = Path(base_path)
    return list(p.glob(file_pattern))


def get_template_dict() -> dict:
    """
    Search for jinja template files(j2 extension) on templates directory and returns a dictionary with
    key=filena_name (without extension) and value=template_full_path
    :return: dictionary with the form: {'git_provider': template_path}
    """
    templates_path = Path(
        pkg_resources.resource_filename("pipeline_generator", "templates"),
    )
    template_path_list = list(templates_path.glob("*.jinja2"))
    templates_dict = {}
    for template_path in template_path_list:
        templates_dict[template_path.stem] = template_path
    return templates_dict


def cleanup_path_list(_path_list: List[Path]) -> List[Path]:
    """
    Remove elements that matches with any regex in IGNORE_RE_LIST
    :param _path_list: list with Path objects
    :return: clean list with Path objects
    """
    clean_path_list = []
    for _path in _path_list:
        if not any(
            ignore_regex_path.match(str(_path))
            for ignore_regex_path in IGNORE_RE_LIST
        ):
            clean_path_list.append(_path)
    return clean_path_list


def get_ci_path_list(_path_list: List[Path]) -> List[CiPath]:
    """
    Search for matches in _path_list with regex in TERRAGRUNT_RE_LIST. If there is a match, a CiPath object is created
    and appended to a list with attributes equals to captured groups in the regular expression.

    :param _path_list: List of Paths
    :return: List of CiPath
    """
    ci_path_list = []
    clean_path_list = cleanup_path_list(_path_list)
    for _path in clean_path_list:
        for regex_path in TERRAGRUNT_RE_LIST:
            m = regex_path.match(str(_path))
            if m:
                ci_path_list.append(
                    CiPath(_path, **m.groupdict()),
                )  # named groups as keyword arguments
                break
    return sorted(ci_path_list, key=lambda x: x.path)


def get_env_list(_ci_path_list: List[CiPath]) -> List[str]:
    """Return an ordered list with the environments"""
    return sorted(
        set(
            ci_path.environment
            for ci_path in _ci_path_list
            if ci_path.environment
        ),
    )


def get_account_list(_ci_path_list: List[CiPath]) -> List[str]:
    """Return an ordered list with the accounts"""
    return sorted(set(ci_path.account for ci_path in _ci_path_list))


def get_region_list(_ci_path_list: List[CiPath]) -> List[str]:
    """Return an ordered list with the region"""
    return sorted(set(ci_path.region for ci_path in _ci_path_list if ci_path))


def get_runner_list(_ci_path_list: List[CiPath]) -> List[str]:
    """Return an ordered list with the accounts"""
    runner_ids = {}
    path = sorted(
        set(
            ci_path.provider
            for ci_path in _ci_path_list
            if ci_path.environment
        ),
    )
    runner_id = sorted(set(ci_path.account for ci_path in _ci_path_list))
    for runner in runner_id:
        with open(path[0] + "/" + runner + "/account.hcl") as f:
            runner_ids[runner] = hcl.load(f)["locals"]["runner_id"]
    return runner_ids


def get_aws_assume_role(_ci_path_list: List[CiPath]) -> List[str]:
    """Return an ordered list with the accounts"""
    assume_roles = {}
    path = sorted(
        set(
            ci_path.provider
            for ci_path in _ci_path_list
            if ci_path.environment
        ),
    )
    assume_id = sorted(set(ci_path.account for ci_path in _ci_path_list))
    for assume in assume_id:
        with open(path[0] + "/" + assume + "/account.hcl") as f:
            path_role = hcl.load(f)["locals"]
            if "assume_role" in path_role:
                assume_roles[assume] = path_role["assume_role"]
    return assume_roles
