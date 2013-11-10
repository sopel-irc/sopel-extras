from willie import coretasks
from willie.module import commands
import os
import subprocess


@commands('document')
def document(bot, trigger):
    base_dir = bot.config.document.base_dir
    if base_dir[-1] != '/':
        base_dir += '/'
    layout = bot.config.document.layout or 'default'

    with open(os.path.join(base_dir, 'modules.md'), 'w') as f:
        front_matter = '''---\nlayout: {}\ntitle: {} commands list\n---\n\n'''
        f.write(front_matter.format(layout, bot.nick))
        f.write('| Command | Purpose | Example |\n')
        f.write('| ------- | ------- | ------- |\n')

        for command in sorted(bot.doc.iterkeys()):
            doc = bot.doc[command]
            docstring = doc[0].replace('\n\n', '<br />').replace('\n', ' ')
            f.write('| {} | {} | {} |\n'.format(command, docstring, doc[1]))
    command = '%(x)s build -s %(b)s -d %(b)s_site -p %(b)s_plugins --layouts %(b)s_layouts'
    command = (command %
        {'x': bot.config.document.jekyll_location or 'jekyll',
         'b': base_dir})
    print command
    subprocess.call(command.split(' '))
    bot.say('Finished processing documentation.')
