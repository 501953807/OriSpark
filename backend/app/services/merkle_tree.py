"""Merkle Tree 批量存证服务 (P1.2.1).

构建 Merkle 树来批量化作品哈希锚定，生成 Merkle Root 和各作品的证明路径。
"""

import hashlib
from typing import Optional


def _double_sha256(data: bytes) -> str:
    """双重 SHA-256 (Bitcoin-style)."""
    return hashlib.sha256(hashlib.sha256(data).digest()).hexdigest()


def _hash_pair(left: str, right: str) -> str:
    """对两个 hash 进行组合后再双 SHA-256."""
    combined = bytes.fromhex(left) + bytes.fromhex(right)
    return _double_sha256(combined)


class MerkleTree:
    """Merkle 树结构.

    存储:
    - leaves: 原始哈希列表
    - levels: 每层的节点列表 (按层次存储)
    - root: Merkle Root
    """

    def __init__(self, hashes: list[str]):
        if not hashes:
            raise ValueError("hash list must not be empty")

        # Normalize to hex
        self.leaves = [h.lower() for h in hashes]
        self.levels: list[list[str]] = []
        self._build()

    def _build(self):
        """构建 Merkle 树."""
        current_level = self.leaves[:]

        while len(current_level) > 1:
            self.levels.append(current_level[:])
            next_level = []

            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                next_level.append(_hash_pair(left, right))

            current_level = next_level

        # 最后一层是根
        self.levels.append(current_level[:])
        self.root = current_level[0]

    def get_root(self) -> str:
        """返回 Merkle Root."""
        return self.root

    def get_proof(self, leaf_hash: str) -> Optional[dict]:
        """为指定的叶子哈希生成 Merkle 证明路径.

        Returns:
            dict: {
                "leaf": str,         # 叶子哈希
                "leaf_index": int,   # 叶子索引
                "root": str,         # Merkle Root
                "proof": list[dict], # 证明路径 [{position: "left"|"right", hash: str}]
                "tree_depth": int,   # 树深度
                "total_leaves": int, # 叶子总数
            }
            None: 如果 leaf_hash 不在叶子列表中
        """
        leaf_hash = leaf_hash.lower()

        try:
            leaf_index = self.leaves.index(leaf_hash)
        except ValueError:
            return None

        proof = []
        current_index = leaf_index

        # 遍历每一层 (不包括根层)
        for level in self.levels[:-1]:
            if current_index % 2 == 0:
                # 左子节点, 需要右边兄弟
                sibling_index = current_index + 1
                position = "right"
            else:
                # 右子节点, 需要左边兄弟
                sibling_index = current_index - 1
                position = "left"

            if sibling_index < len(level):
                sibling_hash = level[sibling_index]
            else:
                # 奇数节点, 复制自己
                sibling_hash = level[current_index]

            proof.append({
                "position": position,
                "hash": sibling_hash,
            })

            # 移动到上一层
            current_index = current_index // 2

        return {
            "leaf": leaf_hash,
            "leaf_index": leaf_index,
            "root": self.root,
            "proof": proof,
            "tree_depth": len(self.levels),
            "total_leaves": len(self.leaves),
        }

    @staticmethod
    def verify_proof(leaf_hash: str, root: str, proof: list[dict]) -> bool:
        """独立验证 Merkle 证明.

        Args:
            leaf_hash: 要验证的叶子哈希
            root: 期望的 Merkle Root
            proof: 证明路径 [{position: "left"|"right", hash: str}]

        Returns:
            bool: 验证是否通过
        """
        current = leaf_hash.lower()

        for step in proof:
            sibling = step["hash"].lower()
            if step["position"] == "right":
                # current 在左, sibling 在右
                current = _hash_pair(current, sibling)
            else:
                # current 在右, sibling 在左
                current = _hash_pair(sibling, current)

        return current == root.lower()


def build_merkle_tree(hashes: list[str]) -> MerkleTree:
    """从作品哈希列表构建 Merkle 树.

    Args:
        hashes: SHA-256 哈希列表 (hex 字符串)

    Returns:
        MerkleTree 实例
    """
    return MerkleTree(hashes)


def get_merkle_root(hashes: list[str]) -> str:
    """快速获取 Merkle Root (不保留完整树结构)."""
    return MerkleTree(hashes).get_root()


def get_merkle_proof(hash_value: str, hashes: list[str]) -> Optional[dict]:
    """获取指定 hash 在列表中的 Merkle 证明."""
    tree = MerkleTree(hashes)
    return tree.get_proof(hash_value)
