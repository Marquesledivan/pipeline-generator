import click

from pipeline_generator.libs.ci_path_lib import get_template_dict
from pipeline_generator.libs.ci_render import render_ci_template
from pipeline_generator.config.constants import IMAGE_DEFAULT, TAGS_RUNNER

GIT_PROVIDER_DICT = get_template_dict()


@click.command()
@click.version_option()
@click.option('--image-registry', '-i', 'image_registry', type=str, default=IMAGE_DEFAULT,
              help='Registry for default image')
@click.option('--tags_runner', '-i', 'tags_runner', type=str, default=TAGS_RUNNER,
              help='Tags for runner')
@click.option('--provider', '-p', 'git_provider', type=click.Choice(list(GIT_PROVIDER_DICT.keys())), default='gitlab',
              show_default=True, help='Git provider, i.e: gitlab')
@click.option('--out', '-o', 'out_filename', type=str, default='', help='Output file name')
@click.option('--extra-know-host', '-e', 'extra_known_hosts', multiple=True,
              help='Host that will be added to ~/.ssh/known_hosts. i.e: gitlab.com')
@click.option('--branch', '-b', 'branch_name', type=str, default='master', show_default=True, help='Default branch name')
@click.option('--export-aws-vars', 'export_aws_vars', is_flag=True,
              help='Export AWS variables in the script section')
def generate_pipeline(image_registry, out_filename, extra_known_hosts,tags_runner, git_provider, branch_name, export_aws_vars):
    ci_template_rendered = render_ci_template(
        template_path=GIT_PROVIDER_DICT.get(git_provider),
        tags_runner = tags_runner,
        image_registry=image_registry,
        extra_known_hosts=extra_known_hosts,
        branch_name=branch_name,
        export_aws_vars=export_aws_vars,
    )
    if out_filename:
        try:
            with open(out_filename, 'w') as f:
                print(ci_template_rendered, file=f)
        except IOError as err:
            print(f"The file {out_filename} could not be opened: ", err)
            exit(1)
    else:
        print(ci_template_rendered)


if __name__ == '__main__':
    generate_pipeline()
