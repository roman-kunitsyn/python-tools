```python
@dataclass
class Note:
    id: str|None
    text: str
    createdAt: datetimez
```

```python
create_note()
detail_note(node_id: str)
update_note(note_id: str, new_note_obj)
remove_note(id: str)
filter_notes(filter, sorter, pagination)
```

```html
<filter_page>
  <header>
    <title>{PageTitle}</title>
    <toolbar layout="horizontal">
      <button align="left">Create New {Entity}<button>
      <dropdown_button align="right">{Entity} Quick Actions<dropdown_button>
    </toolbar>
  </header>
  <main>
    <filter>
      <filter_form/>
    </filter>
    <sorter>
      <sorter_form />
    </sorter>
    <pagination></pagination>
    <table></table>
  </main>
  <footer></footer>
</filter_page>
```

```html
<create_page> </create_page>
```

```html
<detail_page> </detail_page>
```
