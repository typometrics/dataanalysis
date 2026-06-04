import pickle
from verb_centered_analysis import create_verb_centered_table, filter_and_map_ordering_stats
from verb_centered_model import TableConfig
from verb_centered_formatters import TextTableFormatter
import analysis

d_sizes = pickle.load(open('data/all_langs_position2sizes.pkl', 'rb'))
d_num = pickle.load(open('data/all_langs_position2num.pkl', 'rb'))
d_order = pickle.load(open('data/sentence_disorder_percentages.pkl', 'rb'))

all_avgs = analysis.compute_average_sizes(d_sizes, d_num)
from verb_centered_analysis import compute_sizes_table
position_data, validation_info = compute_sizes_table({'fr': all_avgs['fr']}, table_type='anyotherside', all_langs_position2num={'fr': d_num['fr']})

config = TableConfig(
    show_horizontal_factors=True,
    show_diagonal_factors=True,
    show_ordering_triples=True,
    show_row_averages=True,
    show_marginal_means=True,
    arrow_direction='outward'
)

lang_order = d_order['fr']
mapped = filter_and_map_ordering_stats(lang_order, 'anyother')
print("mapped anyother right 4 2:", mapped.get(('right', 4, 2)))

table = create_verb_centered_table(position_data, config, ordering_stats=mapped, validation_info=validation_info, config_type='anyother')
print(TextTableFormatter(table).format())
