# Markdown Formatting Guide

This comprehensive guide covers all the markdown formatting options available in NOW-LMS for creating rich, well-formatted course content.

## What is Markdown?

Markdown is a lightweight markup language that allows you to format text using simple, readable syntax. NOW-LMS supports standard Markdown with additional extensions for enhanced functionality.

## Basic Text Formatting

### Headers

Use hash symbols (#) to create headers:

```markdown
# Header 1 (Main Title)
## Header 2 (Section Title)
### Header 3 (Subsection)
#### Header 4 (Sub-subsection)
##### Header 5 (Minor heading)
###### Header 6 (Smallest heading)
```

**Result:**
# Header 1 (Main Title)
## Header 2 (Section Title)
### Header 3 (Subsection)
#### Header 4 (Sub-subsection)
##### Header 5 (Minor heading)
###### Header 6 (Smallest heading)

### Text Emphasis

```markdown
**Bold text** or __Bold text__
*Italic text* or _Italic text_
***Bold and italic*** or ___Bold and italic___
~~Strikethrough text~~
```

**Result:**
**Bold text** or __Bold text__
*Italic text* or _Italic text_
***Bold and italic*** or ___Bold and italic___
~~Strikethrough text~~

### Line Breaks and Paragraphs

```markdown
This is the first paragraph.

This is the second paragraph with a line break above.

To add a line break within a paragraph,  
end the line with two spaces.
```

## Lists

### Unordered Lists

```markdown
- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
    - Deeply nested item
- Item 3

* Alternative syntax
* Using asterisks
* Also works fine

+ Another alternative
+ Using plus signs
+ Creates same result
```

**Result:**
- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
    - Deeply nested item
- Item 3

### Ordered Lists

```markdown
1. First item
2. Second item
   1. Nested numbered item
   2. Another nested item
3. Third item

1. You can use 1. for all items
1. Markdown will number them correctly
1. This makes reordering easier
```

**Result:**
1. First item
2. Second item
   1. Nested numbered item
   2. Another nested item
3. Third item

### Task Lists

```markdown
- [x] Completed task
- [ ] Incomplete task
- [x] Another completed task
- [ ] Task to be done
```

**Result:**
- [x] Completed task
- [ ] Incomplete task
- [x] Another completed task
- [ ] Task to be done

## Links and Images

### Links

```markdown
[Link text](https://example.com)
[Link with title](https://example.com "This is a tooltip")
[Relative link to another page](../setup.md)
[Reference-style link][1]

[1]: https://example.com "Reference link"

<https://example.com> (Automatic link)
```

**Result:**
[Link text](https://example.com)
[Link with title](https://example.com "This is a tooltip")

### Images

```markdown
![Alt text](image.jpg)
![Alt text with title](image.jpg "Image title")
![Reference-style image][image1]

[image1]: image.jpg "Reference image"
```

### Advanced Image Options

```markdown
<!-- Image with specific size -->
<img src="image.jpg" alt="Alt text" width="300" height="200">

<!-- Image with alignment -->
<img src="image.jpg" alt="Alt text" style="float: right; margin: 10px;">
```

## Tables

### Basic Tables

```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1    | Data 1   | Data 2   |
| Row 2    | Data 3   | Data 4   |
| Row 3    | Data 5   | Data 6   |
```

**Result:**
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1    | Data 1   | Data 2   |
| Row 2    | Data 3   | Data 4   |
| Row 3    | Data 5   | Data 6   |

### Table Alignment

```markdown
| Left Aligned | Center Aligned | Right Aligned |
|:-------------|:--------------:|--------------:|
| Left         | Center         | Right         |
| Text         | Text           | Text          |
```

**Result:**
| Left Aligned | Center Aligned | Right Aligned |
|:-------------|:--------------:|--------------:|
| Left         | Center         | Right         |
| Text         | Text           | Text          |

## Code Formatting

### Inline Code

```markdown
Use `backticks` for inline code.
You can also use `code` in the middle of a sentence.
```

**Result:**
Use `backticks` for inline code.
You can also use `code` in the middle of a sentence.

### Code Blocks

#### Basic Code Blocks

```markdown
```
This is a basic code block
No syntax highlighting
Multiple lines supported
```
```

#### Syntax-Highlighted Code Blocks

```markdown
```python
def hello_world():
    print("Hello, World!")
    return True
```

```javascript
function helloWorld() {
    console.log("Hello, World!");
    return true;
}
```

```html
<!DOCTYPE html>
<html>
<head>
    <title>Page Title</title>
</head>
<body>
    <h1>Hello, World!</h1>
</body>
</html>
```

```css
.highlight {
    background-color: yellow;
    font-weight: bold;
}
```
```

### Supported Languages for Syntax Highlighting

- `python` - Python code
- `javascript` or `js` - JavaScript
- `html` - HTML markup
- `css` - CSS styles
- `java` - Java code
- `c` - C programming
- `cpp` or `c++` - C++
- `php` - PHP code
- `ruby` - Ruby code
- `bash` or `shell` - Shell scripts
- `sql` - SQL queries
- `json` - JSON data
- `xml` - XML markup
- `yaml` - YAML configuration
- `markdown` or `md` - Markdown syntax

## Blockquotes

### Basic Blockquotes

```markdown
> This is a blockquote.
> It can span multiple lines.
> 
> And include multiple paragraphs.
```

**Result:**
> This is a blockquote.
> It can span multiple lines.
> 
> And include multiple paragraphs.

### Nested Blockquotes

```markdown
> This is the first level of quoting.
>
> > This is a nested blockquote.
> > It appears indented further.
>
> Back to the first level.
```

**Result:**
> This is the first level of quoting.
>
> > This is a nested blockquote.
> > It appears indented further.
>
> Back to the first level.

## Advanced Features

### Horizontal Rules

```markdown
---

***

___

<!-- All create horizontal lines -->
```

**Result:**
---

### HTML Integration

You can use HTML tags for advanced formatting:

```markdown
<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
This is content in a styled div.
</div>

<span style="color: red;">Red text</span>

<details>
<summary>Click to expand</summary>
This content is hidden until clicked.
</details>
```

### Footnotes

```markdown
This text has a footnote[^1].

Another reference[^note].

[^1]: This is the first footnote.
[^note]: This is a named footnote.
```

### Definition Lists

```markdown
Term 1
:   Definition for term 1

Term 2
:   Definition for term 2
:   Another definition for term 2
```

## Special Extensions in NOW-LMS

### Admonitions (Callout Boxes)

```markdown
!!! note
    This is a note admonition.

!!! warning
    This is a warning message.

!!! danger
    This is a danger/error message.

!!! tip
    This is a helpful tip.

!!! info
    This is an information box.

!!! success
    This is a success message.
```

### Collapsible Admonitions

```markdown
??? note "Collapsible Note"
    This content is collapsed by default.
    Click the title to expand.

!!! note "Expanded Note"
    This content is expanded by default.
```

### Tabbed Content

```markdown
=== "Tab 1"
    Content for the first tab.

=== "Tab 2"
    Content for the second tab.

=== "Tab 3"
    Content for the third tab.
```

### Mathematical Expressions

```markdown
Inline math: $E = mc^2$

Block math:
$$
\sum_{i=1}^{n} x_i = x_1 + x_2 + \cdots + x_n
$$
```

## Best Practices for Course Content

### Structure Your Content

1. **Use Headers Hierarchically**: Start with H1, then H2, etc.
2. **Break Up Text**: Use lists, blockquotes, and paragraphs
3. **Add Visual Interest**: Include images, tables, and code blocks
4. **Highlight Important Information**: Use admonitions and emphasis

### Writing Guidelines

1. **Be Concise**: Use clear, direct language
2. **Use Active Voice**: "Click the button" vs "The button should be clicked"
3. **Include Examples**: Show concepts with practical examples
4. **Link Relevant Resources**: Connect to external materials

### Accessibility Considerations

1. **Alt Text for Images**: Always include descriptive alt text
2. **Descriptive Link Text**: Use meaningful link descriptions
3. **Header Structure**: Maintain logical header hierarchy
4. **High Contrast**: Ensure text is readable

### Common Mistakes to Avoid

1. **Mixing Syntax**: Don't mix HTML and Markdown unnecessarily
2. **Missing Spaces**: Remember spaces after list markers and headers
3. **Broken Links**: Test all links before publishing
4. **Inconsistent Formatting**: Use consistent style throughout

## Testing Your Markdown

### Preview Before Publishing

1. **Use Preview Mode**: Most editors have preview functionality
2. **Test on Different Devices**: Check mobile and desktop views
3. **Validate Links**: Ensure all links work correctly
4. **Check Formatting**: Verify tables, lists, and code blocks display correctly

### Common Formatting Issues

- **Tables not aligning**: Check pipe character placement
- **Code not highlighting**: Verify language specification
- **Images not displaying**: Check file paths and alt text
- **Lists not formatting**: Ensure proper spacing and indentation

## Quick Reference

### Essential Syntax Summary

```markdown
# Header
**Bold** *Italic*
[Link](url)
![Image](src)
`inline code`
> Blockquote
- List item
1. Numbered item
| Table | Cell |
```

### Keyboard Shortcuts

Most markdown editors support these shortcuts:
- `Ctrl+B` - Bold
- `Ctrl+I` - Italic
- `Ctrl+K` - Link
- `Ctrl+Shift+C` - Code block
- `Ctrl+Shift+>` - Blockquote

## Next Steps

Now that you understand Markdown formatting:
- [Slideshow Setup](slideshow-setup.md) - Create interactive presentations
- [Certificate Customization](certificate-customization.md) - Design completion certificates
- [Forum and Messaging](forum-messaging.md) - Format discussion content