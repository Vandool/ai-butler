class History:
    def __init__(self):
        self.conversation = []

    @property
    def is_empty(self):
        return len(self.conversation) == 0

    def add_message(self, role: str, message: str) -> None:
        self.conversation.append({"role": role, "message": message})

    def add_human_message(self, message: str) -> None:
        self.add_message("Human", message)

    def add_ai_message(self, message: str) -> None:
        self.add_message("AI", message)

    def add_history(self, other_history: "History") -> None:
        self.conversation.extend(other_history.conversation)

    def get_history(self) -> str:
        history_str = ""
        for entry in self.conversation:
            history_str += f"{entry['role']}: {entry['message']}\n"
        return history_str

    def clear_history(self):
        self.conversation = []

    def __str__(self):
        return self.get_history()


if __name__ == "__main__":
    history = History()
    history.add_human_message("I want to create an appointment.")
    history.add_ai_message("Please provide the summary of the appointment.")
    print(history)
    history.add_history(history)
    print(history)
    history.clear_history()
