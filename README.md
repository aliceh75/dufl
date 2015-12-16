**dufl** is dotfile manager with a simplified git-like workflow.

**Still under development. Not all features described here are implemented! Wait for 0.1 release plz :)**

Features:
- Leaves your dotfiles intact (no moving & symlinking);
- Simplified git-like workflow;
- Security checks (attempts to detect private ssh keys, etc. and prevents uploading them).

Anti-Features:
- Developed in Python, so won't be useful in environments where you can't install Python and Python packages.

h2. Example

```sh
    # Create a ~/.dufl folder linked to the given repository,
    # where versions of dotfiles will be stored.
    dufl init http://github.com/example_user/dotfiles.git

    # Add a file to the git repository, and commit it with
    # the given commit message
    dufl add ~/.vimrc -m "Add my vimrc"

    # Push the repository
    dufl push

    # ... edit ~/.vimrc ...

    # See if we have changed any files
    dufl status

    # Note that until we add it again, the changes to ~/.vimrc
    # do *not* get pushed to the git repository. The following
    # does nothing:
    dufl push

    # We need to add it again. This ensures we don't push changes
    # by mistake!
    dufl add ~/.vimrc -m "Use soft tabs"
    dufl push
```

h2. Commands

h3. dufl init

Creates a local dufl folder (by default `~/.dufl`) and link it to the given git repository. If the given repository already contains files, then they are pulled. If not **dufl** initializes the folder with empty directories and a settings file with default values for your environment.

Example:
```
    dufl init http://github.com/example_user/dotfiles.git
```

If the repository doesn't yet exist upstream, you will get an error from git - but that's fine, you can continue using dufl and create the repository later (before your first push!)

h3. dufl add

`dufl add` adds and commits a file.

Following the git workflow, dufl does not automatically commit modifications to your files. You must explicetly add a file for it to be managed by dufl, and for every change you make to the file you must add it again. This ensures you always know what it being sent to the git repository - important if it is a public one.

Example:
```
    dufl add ~/.vimrc -m "Use soft tabs"
```

The commit message is optional, and defaults to "Update.".

h3. dufl push

Push all commited changes to the upstream git repository.

h3. dufl status

Shows all files that have local modifications

Example:
```
    dufl status
```

h3. dufl diff

Shows the changes made to a particular file.

Example:
```
    dufl diff ~/.vimrc
```

h2. Installation

```sh
    git clone https://github.com/aliceh75/dufl.git
    cd dufl
    pip install -r requirements.txt
    pip install .
```

h2. Testing

Make sure you install development requirements:

```sh
    pip install -r dev_requirements.txt
```

And run `py.test`:

```sh
    py.test dufl/tests
```
