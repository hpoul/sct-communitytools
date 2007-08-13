from sphene.community.sphutils import add_setting_defaults



add_setting_defaults( {
    'board_count_views': True,
    'board_heat_days': 30,
    'board_heat_post_threshold': 10,
    'board_heat_view_threshold': 10,
    'board_heat_calculator': 'sphene.sphboard.models.calculate_heat',


    'workaround_select_related_bug': False,
    })
