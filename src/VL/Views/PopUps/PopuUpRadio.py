from src.DL.Config import CF_RADIO_MISSING_BOOKING_CODES_ALL, CF_RADIO_MISSING_BOOKING_CODES_WITH_COUNTER_ACCOUNT
from src.VL.Views.PopUps.PopUp import PopUp, BLOCK_TITLE, BLOCK_BUTTONS, BLOCK_OPTION_TEXT


class PopUpRadio(PopUp):

    def _get_popup_layout(
            self, block_name=None, hide_option=False, buttons=True) -> list:
        block_radio = [
                self.frame('Dialog_radios', [
                    self.radio(key=CF_RADIO_MISSING_BOOKING_CODES_ALL, group_id=1),
                    self.radio(key=CF_RADIO_MISSING_BOOKING_CODES_WITH_COUNTER_ACCOUNT, group_id=1),
                ], border_width=1, expand_y=True, expand_x=True),
            ]
        # Title
        layout = super()._get_popup_layout(BLOCK_TITLE)
        # Radio buttons
        layout.extend(block_radio)
        # Buttons OK/CANCEL
        layout.extend(super()._get_popup_layout(BLOCK_BUTTONS))
        # Option to hide next time
        if hide_option:
            layout.extend(super()._get_popup_layout(BLOCK_OPTION_TEXT))
        return layout
