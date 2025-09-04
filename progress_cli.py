'''
    Prints progressbar to cli
    Useful for displaying multithread progress
'''

import os

def _progress_percentage(perc, width=None):
    # This will only work for python 3.3+ due to use of
    # os.get_terminal_size the print function etc.

    FULL_BLOCK = '█'
    # this is a gradient of incompleteness
    INCOMPLETE_BLOCK_GRAD = ['░', '▒', '▓']
    
    assert(isinstance(perc, float))
    assert(0. <= perc <= 100.)
    # if width unset use full terminal
    if width is None:
        width = os.get_terminal_size().columns - 5
    # progress bar is block_widget separator perc_widget : ####### 30%
    max_perc_widget = '[100.00%]' # 100% is max
    separator = ' '
    blocks_widget_width = width - len(separator) - len(max_perc_widget)
    assert(blocks_widget_width >= 10) # not very meaningful if not
    perc_per_block = 100.0/blocks_widget_width
    # epsilon is the sensitivity of rendering a gradient block
    epsilon = 1e-6
    # number of blocks that should be represented as complete
    full_blocks = int((perc + epsilon)/perc_per_block)
    # the rest are "incomplete"
    empty_blocks = blocks_widget_width - full_blocks

    # build blocks widget
    blocks_widget = ([FULL_BLOCK] * full_blocks)
    blocks_widget.extend([INCOMPLETE_BLOCK_GRAD[0]] * empty_blocks)
    # marginal case - remainder due to how granular our blocks are
    remainder = perc - full_blocks*perc_per_block
    # epsilon needed for rounding errors (check would be != 0.)
    # based on reminder modify first empty block shading
    # depending on remainder
    if remainder > epsilon:
        grad_index = int((len(INCOMPLETE_BLOCK_GRAD) * remainder)/perc_per_block)
        blocks_widget[full_blocks] = INCOMPLETE_BLOCK_GRAD[grad_index]

    # build perc widget
    str_perc = '%.2f' % perc
    # -1 because the percentage sign is not included
    perc_widget = '[%s%%]' % str_perc.ljust(len(max_perc_widget) - 3)

    # form progressbar
    progress_bar = '%s%s%s' % (''.join(blocks_widget), separator, perc_widget)
    # return progressbar as string
    return ''.join(progress_bar)


def copy_progress(indx, copied, total):
    # Move the cursor to the top left
    print('\033[H', end='')
    # Print 2 newlines per index, the progress, then a newline for the filename
    # followed by a line clear so the names dont stay, then the actual filename
    print('\n\n' * indx + _progress_percentage(100*copied/total) +
          '\n\033[K', end='')


def clear_console():
    """Clears the console screen."""
    if os.name == 'nt':  # For Windows
        os.system('cls')
    else:  # For macOS and Linux
        os.system('clear')