from pathlib import Path

import streamlit as st


GALLERY_DIR = Path(__file__).parent / "assets" / "campus"

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}


def get_campus_images():
    """Return all supported photographs in the campus gallery folder."""
    if not GALLERY_DIR.exists():
        return []

    return sorted(
        [
            image
            for image in GALLERY_DIR.iterdir()
            if image.is_file() and image.suffix.lower() in SUPPORTED_FORMATS
        ],
        key=lambda image: image.name.lower()
    )


def get_image_caption(image):
    """Create a readable caption from an image filename."""
    return image.stem.replace("_", " ").replace("-", " ").title()


def show_campus_gallery():
    """Display the CampusFlow campus photograph gallery."""

    st.title("📸 Campus Gallery")

    st.markdown(
        """
        Explore photographs of the University of Jos campus, its
        learning spaces, libraries, buildings and environment.
        """
    )

    st.divider()

    images = get_campus_images()

    if not images:
        st.info(
            "The gallery is ready. Add photographs to "
            "`assets/campus/` to display them here."
        )
        return

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Photographs", len(images))

    with col2:
        st.metric("Gallery", "University of Jos")

    search = st.text_input(
        "🔎 Search photographs",
        placeholder="Search library, campus, buildings..."
    )

    if search.strip():
        images = [
            image for image in images
            if search.lower() in get_image_caption(image).lower()
        ]

    if not images:
        st.warning("No photographs match your search.")
        return

    st.divider()

    columns = st.columns(3)

    for index, image in enumerate(images):
        with columns[index % 3]:
            st.image(
                str(image),
                caption=get_image_caption(image),
                use_container_width=True
            )

    st.divider()

    st.caption(
        "CampusFlow | University of Jos Campus Gallery"
    )
