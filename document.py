from willie import coretasks
from willie.module import commands
import os

start = """
<!DOCTYPE=HTML>
<html lang="en">
<head>
    <title>{title}</title>
    <meta charset="utf-8">
    {stylesheets}
</head>
<body>
"""

default_css = """
<style type="text/css">
table.commands {
    border-width: 1px;
    border-collapse: collapse;
    padding: 1px 1px;
}
table.commands td {
    border-width: 1px;
    padding: 5px 10px;
    border-style: solid;
}
</style>
"""

@commands('document')
def document(bot, trigger):
    title = bot.config.document.page_title or '{} Commands List'.format(bot.nick)
    stylesheets = ''
    if bot.config.document.stylesheets:
        for sheet in bot.config.document.get_list('stylesheets'):
            stylesheets += '<link href="{}" rel="stylesheet">\n'.format(sheet)

    with open(bot.config.document.commands_file, 'w') as f:
        f.write(start.format(title=title, stylesheets=stylesheets))
        if not stylesheets:
            f.write(default_css)

        #TODO allow including some sort of header here
        # Make the actual commands table
        f.write('<table class="commands">')
        for command in sorted(bot.doc.iterkeys()):
            doc = bot.doc[command]
            f.write('<tr><td><a name="{command}">{command}</a></td><td>{purpose}</td><td>{example}</td></tr>\n'.format(
                    command=command, purpose=doc[0], example=doc[1]))
        f.write('</table>')
        #TODO allow including some sort of footer here.
        f.write('</html>')
