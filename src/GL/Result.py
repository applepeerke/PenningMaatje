from src.GL.BusinessLayer.LogManager import Singleton as Log
from src.GL.Const import EMPTY
from src.GL.Enums import ResultCode, MessageSeverity, ActionCode

SEVERITY_ERROR = ('error', 'exception', 'sqlexception')
SEVERITY_WARNING = ('warning', 'cancel')
SEVERITY_INFO = ('info', 'ok', 'completion')

MNEMONIC = {
    MessageSeverity.Error: 'E ',
    MessageSeverity.Completion: 'C ',
    MessageSeverity.Warning: 'W ',
    MessageSeverity.Info: 'I '
}

log_cache = []


class ResultMessage(object):

    @property
    def message(self):
        return self._message

    @property
    def severity(self):
        return self._severity

    def __init__(self, message, severity):
        self._message = message
        self._severity = severity


class BoxResult(object):

    @property
    def message(self):
        return self._message

    @property
    def max_severity(self):
        return self._max_severity

    @property
    def is_completion_message(self):
        return self._is_completion_message

    def __init__(self, message, max_severity=MessageSeverity.Info, is_completion_message=False):
        self._message = message
        self._max_severity = max_severity
        self._is_completion_message = is_completion_message


class Result(object):

    @property
    def code(self):
        return self._code

    @property
    def action_code(self):
        return self._action_code

    """ Result codes """

    @property
    def OK(self):
        return self._code in (ResultCode.Ok, ResultCode.Equal)

    @property
    def WA(self):
        return self._code in (ResultCode.Warning, ResultCode.NotFound)

    @property
    def ER(self):
        return self._code == ResultCode.Error

    @property
    def CN(self):
        return self._code == ResultCode.Canceled

    @property
    def EX(self):
        return self._code == ResultCode.Exit

    """ Action codes """

    @property
    def RT(self):
        return self._action_code == ActionCode.Retry

    @property
    def GO(self):
        return self._action_code == ActionCode.Go

    @property
    def CL(self):
        return self._action_code == ActionCode.Close

    @property
    def text(self):
        return self._text

    @property
    def result_value(self):
        return self._value

    @property
    def severity(self):
        return self._severity

    @property
    def messages(self):
        return self._messages

    """
    Setters
    """

    @code.setter
    def code(self, value):
        self._code = value
        self._severity = self._code_to_severity(value)

    @action_code.setter
    def action_code(self, value):
        self._set_action_code(value)

    @text.setter
    def text(self, value):
        self._text = value

    @result_value.setter
    def result_value(self, value):
        self._value = value

    @severity.setter
    def severity(self, value):
        self._severity = value
        self._code = self.severity_to_code(value)

    @messages.setter
    def messages(self, value):
        self._messages = value

    def __init__(self, code=ResultCode.Ok, text=EMPTY, severity: MessageSeverity = None, action_code=None):
        self._code = code
        self._text = text
        self._severity = severity
        self._set_action_code(action_code)

        self._value = EMPTY
        self._messages = []
        self._messages_raw = set()
        if severity:
            self._code = self.severity_to_code(severity)
        else:
            self._severity = self._code_to_severity(code)
        if text:
            log(text, sev=self._severity)

    def _set_action_code(self, value):
        self._action_code = value
        if value == ActionCode.Cancel:
            self._text = 'Actie is geannuleerd.'
            self._code = ResultCode.Canceled

    def add_message(self, message, severity=MessageSeverity.Info, log_message=True):
        """
        Result.text is treated as a completion/error message.
        All messages are added to Result.messages.
        """
        if log_message:
            log(message, sev=severity)
        p_severity = self._code_to_severity(self._code)
        p_completion_message = self._text
        if severity in (MessageSeverity.Error, MessageSeverity.Warning, MessageSeverity.Completion):
            # Set This code and severity
            self._code = self.severity_to_code(severity)
            self._severity = self._code_to_severity(self._code)
        # Move old completion text to messages.
        if p_completion_message and p_completion_message != self._text:
            self._add_unique_message(p_completion_message, p_severity)
        # Add the new message
        self._add_unique_message(message, severity)

    def _add_unique_message(self, message, severity):
        if message and message not in self._messages_raw:
            self._messages.append(ResultMessage(message, severity))
            self._messages_raw.add(message)

    def add_messages(self, messages: [ResultMessage]):
        """ Add messages to Result.Messages - without logging. """
        [self.add_message(m.message, severity=m.severity, log_message=False) for m in messages]

    def yield_messages(self, min_severity: MessageSeverity = 0) -> [ResultMessage]:
        """ Purpose: "bubble up" messages to higher level result """
        result_messages = []
        for M in self._messages:
            if M.severity >= min_severity:
                result_messages.append(M)
        # Add completion message
        if self._text:
            result_messages.append(ResultMessage(self._text, self._code_to_severity(self._code)))
        return result_messages

    def get_messages_as_message(self, max_lines=20, sophisticate=True) -> str:
        """
        sophisticate: self._text is considered a completion message.
        messages may start with mnemonic ("C ", "E ", "I " or "W" ).
        """
        if not self._messages or max_lines < 1:
            return EMPTY
        suffix = '\n...' if len(self._messages) > max_lines else EMPTY
        sophisticate = False if not self._text else sophisticate

        # Concatenate the messages
        message = EMPTY
        for i in range(min(len(self._messages), max_lines)):
            m = self._messages[i].message
            # Remove other Completion messages (optional)
            if sophisticate and len(m) > 2 and m[:2] == MNEMONIC[MessageSeverity.Completion]:
                continue
            # Remove mnemonic (optional)
            if sophisticate and len(m) > 2 and m[:2] in MNEMONIC.values():
                m = m[2:]
            if not self._text or self._text not in m:
                message = f'{message}\n{m}' if message else m
        # Output
        # - Both text and messages
        if message and self._text:
            return f'{self._text}\n{message}{suffix}'
        # - Only messages
        elif message:
            return f'{message}{suffix}'
        # - Only text (or no text)
        else:
            return self._text

    def severity_to_code(self, severity: MessageSeverity) -> str:
        if self._action_code == ActionCode.Cancel:
            return ResultCode.Canceled
        if severity == MessageSeverity.Error:
            return ResultCode.Error
        elif severity == MessageSeverity.Warning:
            return ResultCode.Warning if self._code != ResultCode.Error else self._code
        elif severity in (MessageSeverity.Info, MessageSeverity.Completion):
            return ResultCode.Ok if self._code not in (ResultCode.Error, ResultCode.Warning) else self._code
        else:
            raise ValueError(f'{__name__}: Severity "{severity}" can not be mapped to Result.')

    @staticmethod
    def _code_to_severity(code) -> MessageSeverity:
        if code in (ResultCode.Error, ResultCode.Canceled, ResultCode.Exit):
            return MessageSeverity.Error
        elif code in (ResultCode.Warning, ResultCode.NotFound):
            return MessageSeverity.Warning
        elif code in (ResultCode.Ok, ResultCode.Equal):
            return MessageSeverity.Info
        else:
            raise ValueError(f'{__name__}: Severity "{code}" can not be mapped to Result.')

    def get_box_message(self, min_severity=MessageSeverity.Error, cont_text=False) -> bool:
        """ return: Confirmed flag """
        from src.VL.Windows.General.MessageBox import message_box
        severity = self._severity
        box_result: BoxResult = self._get_message_box_result(min_severity)
        severity = int(max(str(severity), str(box_result.max_severity)))
        # No alarm when warnings (20) are to be ignored.
        if severity < min_severity:
            severity = MessageSeverity.Completion if box_result.is_completion_message \
                else MessageSeverity.Info
        return message_box(box_result.message, severity=severity, cont_text=cont_text)

    def _get_message_box_result(
            self, min_severity=MessageSeverity.Error, max_lines=20, sophisticate=True, dft=EMPTY) -> BoxResult:
        """
        sophisticate by default (i.e. without mnemonic) or:
            self._text is a completion message.
            (messages may start with mnemonic ("C ", "E ", "I " or "W" )).
        """
        if (not self._messages or max_lines < 1) and not self._text:
            return BoxResult(dft)

        sophisticate = False if sophisticate is True and self._text else sophisticate

        # Concatenate the messages
        message = EMPTY
        max_severity = MessageSeverity.Info
        is_completion_message = True

        # Start with (Completion) message in attribute "text".
        if self._text:
            message = self._text

        filtered_messages_count = 0
        filtered_warnings_count = 0
        filtered_errors_count = 0

        for i in range(len(self._messages)):
            M = self._messages[i]
            # Max severity (ignore completion to calculate this)
            if M.severity != MessageSeverity.Completion and M.severity > max_severity:
                max_severity = M.severity

            # Optionally ignore Info messages
            if M.severity < min_severity:
                if M.severity == MessageSeverity.Warning:
                    filtered_warnings_count += 1
                elif M.severity == MessageSeverity.Error:
                    filtered_errors_count += 1
                continue

            # Max lines?
            filtered_messages_count += 1
            if filtered_messages_count > max_lines:
                break

            # Add the message
            text = M.message
            # Add mnemonic (optional)
            if not sophisticate:
                mnemonic = MNEMONIC.get(M.severity)
                text = f'{mnemonic}{text}' if mnemonic else text
            # Skip message if in attribute "text" (Completion).
            if self._text and self._text in text:
                continue
            # Remember if Not completion.
            if M.severity != MessageSeverity.Completion:
                is_completion_message = False
            message = f'{message}\n{text}' if message else text

        # Output
        # A. Warnings/errors found but not shown.
        if filtered_warnings_count > 0 or filtered_errors_count > 0:
            if len(self._messages) == 1:
                message = self._messages[0].message
            else:
                warning_text = f'{filtered_warnings_count} waarschuwingen'if filtered_warnings_count > 0 else EMPTY
                error_text = f'{filtered_errors_count} fouten'if filtered_errors_count > 0 else EMPTY
                en = ' en ' if filtered_warnings_count > 0 and filtered_errors_count > 0 else EMPTY
                message = f'{message}\n\nEr zijn ' \
                          f'{warning_text}{en}' \
                          f'{error_text} gevonden.' \
                          f'\nVoor meer informatie, zie de log.\n'
        # B. There are 1-n messages
        else:
            # "text" is then a title.
            suffix = '\n...' if filtered_messages_count > max_lines else EMPTY
            message = self._text or f'{message}{suffix}'
        return BoxResult(message, max_severity, is_completion_message)


def log(line, color=None, new_line=True, sev=MessageSeverity.Info, log_started=False) -> bool:
    global log_cache
    printed = False
    if line:
        if Log().log_file_name:
            Log().add_coloured_line(line, color, new_line, sev)
            # After creating log header the cache should be listed.
            if log_cache and log_started:
                [Log().add_coloured_line(line) for line in log_cache]
                log_cache = []
                printed = True
        else:
            # Before log has started, print and cache the line for diagnostic purposes.
            log_cache.append(line)
            print(line)
            printed = True
    return printed
