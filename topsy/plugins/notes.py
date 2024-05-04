import imgui

from pathlib import Path
from pydantic import BaseModel
from marko import inline, block, Markdown, MarkoExtension


class Checkbox(inline.InlineElement):
    pattern = r"\[([ x]?)\]"

    @property
    def checked(self):
        return self.children == "x"


CheckboxExt = MarkoExtension(
    elements=[
        Checkbox,
    ],
)


class TodoItem(BaseModel):
    checked: bool = False
    text: str


class TodoNote(BaseModel):
    path: Path
    title: str
    items: list[TodoItem]


class Plugin:
    def __init__(self, notes_directory: str, **kwargs):
        self._notes_dir = Path(notes_directory).expanduser().absolute()
        self._md = Markdown(extensions=[CheckboxExt])
        self._notes = self._load_notes()
        self._new_item_text = ""

    def _load_note(self, note_path: Path):
        title = note_path.name
        items = []
        doc = self._md.parse(note_path.read_text())

        def render_raw_text(raw_text: inline.RawText) -> str:
            return raw_text.children.strip()

        def render_heading(heading: block.Heading) -> str:
            return " ".join([render_raw_text(child) for child in heading.children])

        def get_items(list: block.List) -> list[TodoItem]:
            items = []
            for child in list.children:
                list_item: block.ListItem = child
                p: block.Paragraph = list_item.children[0]
                c1, c2 = p.children
                checkbox: Checkbox = c1
                text: inline.RawText = c2
                items.append(
                    TodoItem(checked=checkbox.checked, text=render_raw_text(text))
                )
            return items

        for child in doc.children:
            type_ = child.get_type(snake_case=True)

            if type_ == "heading":
                title = render_heading(child)

            if type_ == "list":
                items = get_items(child)

        return TodoNote(path=note_path, title=title, items=items)

    def _load_notes(self):
        # TODO: Remove this
        assert self._notes_dir.exists()
        if not self._notes_dir.exists():
            self._notes_dir.mkdir(parents=True)

        return [self._load_note(p) for p in self._notes_dir.rglob("**/*.md")]

    def process(self):
        for note in self._notes:
            with imgui.begin(note.title, flags=imgui.WINDOW_NO_COLLAPSE) as window:
                if window.expanded:
                    to_delete = []
                    for i, item in enumerate(note.items):
                        with imgui.styled(
                            imgui.STYLE_ALPHA, 0.1 if item.checked else 1.0
                        ):
                            _, item.checked = imgui.checkbox(item.text, item.checked)

                        with imgui.begin_popup_context_item() as context_menu:
                            if context_menu.opened:
                                _, delete_selected = imgui.selectable("Delete")
                                if delete_selected:
                                    to_delete.append(item)

                    for item in to_delete:
                        note.items.remove(item)

                    imgui.push_item_width(-1)
                    changed, self._new_item_text = imgui.input_text_with_hint(
                        "New Item:",
                        "Type new note here",
                        self._new_item_text,
                        flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE,
                    )
                    if changed:
                        note.items.append(TodoItem(text=self._new_item_text))
                        self._new_item_text = ""
                    imgui.pop_item_width()

    def close(self):
        for note in self._notes:
            lines = [f"# {note.title}\n"]
            for item in note.items:
                lines.append(f"- [{'x' if item.checked else ' '}] {item.text}")
            with note.path.open("w") as note_out:
                for line in lines:
                    note_out.write(line + "\n")
